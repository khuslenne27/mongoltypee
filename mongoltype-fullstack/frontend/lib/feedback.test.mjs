import {test} from 'node:test';
import assert from 'node:assert/strict';
import {clusterFeedback,nextExpected,controlLabels} from './feedback.ts';

test('base letter awaits FVS rather than showing an error prematurely',()=>{
 assert.equal(clusterFeedback('ᠠ\u180b','ᠠ',true),'pending');
 assert.equal(clusterFeedback('ᠠ\u180b','ᠠ\u180b',true),'correct');
 assert.equal(clusterFeedback('ᠠ\u180b','ᠠ\u180c',true),'error');
});
test('missing FVS becomes an error once another cluster or word was entered',()=>{
 assert.equal(clusterFeedback('ᠠ\u180b','ᠠ',false),'error');
 assert.equal(clusterFeedback('ᠠ\u180b','ᠡ',true),'error');
});
test('next key identifies selectors and MVS without skipping them',()=>{
 assert.equal(nextExpected('ᠠ\u180bᠪ\u180eᠠ','ᠠ'),'\u180b');
 assert.equal(nextExpected('ᠠ\u180bᠪ\u180eᠠ','ᠠ\u180bᠪ'),'\u180e');
 assert.ok(controlLabels['\u180b'].includes('FVS1'));
});
test('NNBSP stays within a word while ordinary space advances to the next word',()=>{
 assert.equal(nextExpected('ᠨᠣᠮ\u202fᠤᠨ ᠠᠪᠤ','ᠨᠣᠮ'),'\u202f');
 assert.equal(nextExpected('ᠨᠣᠮ\u202fᠤᠨ ᠠᠪᠤ','ᠨᠣᠮ\u202fᠤᠨ '),'ᠠ');
});
