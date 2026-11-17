import {test} from 'node:test';
import assert from 'node:assert/strict';
import {Attempt} from './attempt.ts';

const payload={session_id:'one',typed_text:'book',elapsed_ms:30000};
test('retries a rejected start and saves the original result',async()=>{
  const calls=[];let starts=0;
  const attempt=new Attempt('one',async(path,body)=>{
    calls.push([path,body]);
    if(path.endsWith('/start')&&++starts===1)throw Error('offline');
    return {saved:true};
  });
  await assert.rejects(attempt.start(),/offline/);
  assert.deepEqual(await attempt.save(payload),{saved:true});
  assert.deepEqual(calls.map(c=>c[0]),['/tests/one/start','/tests/one/start','/results']);
  assert.deepEqual(calls[1][1],{recover:true});
  assert.deepEqual(calls[2][1],payload);
});
test('lost result response can retry without restarting the server clock',async()=>{
  let starts=0,results=0;
  const attempt=new Attempt('one',async(path)=>{
    if(path.endsWith('/start'))starts++;
    if(path==='/results'&&++results===1)throw Error('response lost');
    return {id:5};
  });
  await attempt.start();
  await assert.rejects(attempt.save(payload),/response lost/);
  assert.deepEqual(await attempt.save(payload),{id:5});
  assert.equal(starts,1);
});
test('waits for the final checkpoint and coalesces concurrent save clicks',async()=>{
  const calls=[];
  const attempt=new Attempt('one',async(path,body)=>{calls.push([path,body]);return {saved:true};});
  const checkpoint=attempt.checkpoint('book');
  const first=attempt.save(payload),second=attempt.save(payload);
  assert.equal(first,second);
  await Promise.all([checkpoint,first]);
  assert.deepEqual(calls.map(c=>c[0]),['/tests/one/start','/tests/one/checkpoint','/results']);
});
test('restarted attempts retain separate session ids and payloads',async()=>{
  const calls=[];const send=async(path,body)=>{calls.push([path,body]);return {};};
  const old=new Attempt('old',send),current=new Attempt('current',send);
  await old.start();await current.start();
  await old.save({...payload,session_id:'old'});
  await current.save({...payload,session_id:'current'});
  assert.deepEqual(calls.filter(c=>c[0]==='/results').map(c=>c[1].session_id),['old','current']);
});
test('failed start followed by checkpoint recovery remains a recovery start',async()=>{
  const recover=[];
  const attempt=new Attempt('one',async(path,body)=>{
    if(path.endsWith('/start')){recover.push(body.recover);if(recover.length===1)throw Error('lost');}
    return {};
  });
  await assert.rejects(attempt.start());
  await attempt.checkpoint('book',true);
  await attempt.save(payload);
  assert.deepEqual(recover,[false,true]);
});
test('slow checkpoints are coalesced but the final text is still sent',async()=>{
  const texts=[];let release;
  const blocked=new Promise(resolve=>{release=resolve;});
  const attempt=new Attempt('one',async(path,body)=>{
    if(path.endsWith('/checkpoint')){texts.push(body.typed_text);if(texts.length===1)await blocked;}
    return {};
  });
  const first=attempt.checkpoint('b');
  const skipped=attempt.checkpoint('bo');
  const final=attempt.checkpoint('book',true);
  release();await Promise.all([first,skipped,final]);
  assert.deepEqual(texts,['b','book']);
});
