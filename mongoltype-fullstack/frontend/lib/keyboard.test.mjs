import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {keyHint,keyOutput,standard,physicalEdit,vowelNames} from './keyboard.ts';

const event=(code,shiftKey=false)=>({code,shiftKey,ctrlKey:false,altKey:false,metaKey:false,isComposing:false});
test('all seven vowels map identically on physical and screen keys in both layouts',()=>{
 for(const layout of ['standard','legacy']){
  const keys={KeyA:'ᠠ',KeyE:'ᠡ',KeyI:'ᠢ',[layout==='legacy'?'KeyW':'KeyQ']:'ᠣ',KeyV:'ᠤ',KeyO:'ᠥ',KeyU:'ᠦ'};
  for(const [code,expected] of Object.entries(keys)){
   const key=standard.flat().find(k=>k.code===code);
   assert.equal(keyOutput(key,layout),expected);
   // event.key can differ under the OS layout; the site uses physical code.
   assert.equal(physicalEdit({...event(code),key:'wrong OS vowel'},'',0,0,layout).text,expected);
   assert.ok(vowelNames[expected]);
   assert.equal(keyHint(expected,layout),code.slice(3));
  }
 }
});
test('identical-looking O/U and OE/UE stay distinct',()=>{
 assert.notEqual(physicalEdit(event('KeyQ'),'',0,0,'standard').text,physicalEdit(event('KeyV'),'',0,0,'standard').text);
 assert.notEqual(physicalEdit(event('KeyO'),'',0,0,'standard').text,physicalEdit(event('KeyU'),'',0,0,'standard').text);
});
test('all 1504 dictionary spellings can be entered with the indicated physical keys',()=>{
 const rows=JSON.parse(readFileSync(new URL('../../backend/data/khudam/words.json',import.meta.url),'utf8'));
 for(const layout of ['standard','legacy']){
  const reverse=new Map();
  for(const shifted of [false,true])for(const key of standard.flat()){
   const value=keyOutput(key,layout,shifted);
   if(!reverse.has(value))reverse.set(value,event(key.code,shifted));
  }
  for(const row of rows){
   let text='';
   for(const character of row.text){
    const key=reverse.get(character);
    assert.ok(key,`${layout}: missing U+${character.codePointAt(0).toString(16)}`);
    const next=physicalEdit(key,text,text.length,text.length,layout);
    assert.ok(next);text=next.text;
   }
   assert.equal(text,row.text);
  }
 }
});
test('selector correction and selected text replacement preserve neighboring vowels',()=>{
 assert.deepEqual(physicalEdit(event('Backspace'),'ᠠ\u180b',2,2,'standard'),{text:'ᠠ',caret:1});
 assert.deepEqual(physicalEdit(event('KeyV'),'ᠨᠣᠮ',1,2,'standard'),{text:'ᠨᠤᠮ',caret:2});
 assert.equal(physicalEdit(event('Quote',true),'',0,0,'standard').text,'\u180c');
});
test('shortcuts and IME composition are not intercepted',()=>{
 for(const extra of [{ctrlKey:true},{metaKey:true},{altKey:true},{isComposing:true}]){
  assert.equal(physicalEdit({...event('KeyA'),...extra},'',0,0,'standard'),null);
 }
 assert.equal(physicalEdit(event('ArrowLeft'),'',0,0,'standard'),null);
});
test('Mongolian number exercises map all ten digits, hints and numpad identically',()=>{
 for(const layout of ['standard','legacy'])for(let n=0;n<=9;n++){
  const expected=String.fromCodePoint(0x1810+n);
  const key=standard.flat().find(k=>k.code===`Digit${n}`);
  assert.equal(keyOutput(key,layout,false,true),expected);
  assert.equal(keyHint(expected,layout,true),String(n));
  assert.equal(physicalEdit(event(`Digit${n}`),'',0,0,layout,true).text,expected);
  assert.equal(physicalEdit(event(`Numpad${n}`),'',0,0,layout,true).text,expected);
  assert.equal(keyOutput(key,layout,false),String(n));
 }
});
test('number exercise preserves shifted punctuation and scores distinct digit code points',()=>{
 for(const layout of ['standard','legacy']){
  const key=standard.flat().find(k=>k.code==='Digit1');
  assert.equal(keyOutput(key,layout,true,true),keyOutput(key,layout,true));
  let text='';
  for(const n of [1,0,2])text=physicalEdit(event(`Digit${n}`),text,text.length,text.length,layout,true).text;
  assert.equal(text,'᠑᠐᠒');
 }
});
