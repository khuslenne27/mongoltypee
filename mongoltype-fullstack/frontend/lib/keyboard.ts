// Layout data: Unicode CLDR 43; see NOTICE.md.
export type KeyboardLayout='standard'|'legacy';
export const vowelNames:Record<string,string>={
 'ᠠ':'А (a)','ᠡ':'Э (e)','ᠢ':'И (i)','ᠣ':'О (o)','ᠤ':'У (u)','ᠥ':'Ө (ö)','ᠦ':'Ү (ü)','ᠧ':'Е (ē)',
};
export type Key={code:string;latin:string;normal:string;shift?:string;wide?:number};
const letters=(latin:string,normal:string)=>latin.split('').map((l,i)=>({code:'Key'+l,latin:l,normal:Array.from(normal)[i]}));
export const standard:Key[][]=[
 [{code:'Backquote',latin:'`',normal:'\u180d',shift:'~'},...'1234567890'.split('').map((n,i)=>({code:'Digit'+n,latin:n,normal:n,shift:['︕','⁈','⁉','—','%','\u200c','᠊','\u200d','(',')'][i]})),{code:'Minus',latin:'-',normal:'\u202f',shift:'\u180e'},{code:'Equal',latin:'=',normal:'=',shift:'+'},{code:'Backspace',latin:'⌫',normal:'⌫',wide:1.8}],
 [{code:'Tab',latin:'Tab',normal:'Tab',wide:1.3},...letters('QWERTYUIOP','ᠣᠸᠡᠷᠲᠶᠦᠢᠥᠫ'),{code:'BracketLeft',latin:'[',normal:'[',shift:'〈'},{code:'BracketRight',latin:']',normal:']',shift:'〉'},{code:'Backslash',latin:'\\',normal:'᠁',shift:'︱'}],
 [{code:'CapsLock',latin:'Caps',normal:'Caps',wide:1.6},...letters('ASDFGHJKL','ᠠᠰᠳᠹᠭᠬᠵᠺᠯ'),{code:'Semicolon',latin:';',normal:'︔',shift:'᠄'},{code:'Quote',latin:"'",normal:'\u180b',shift:'\u180c'},{code:'Enter',latin:'Enter',normal:'Enter',wide:1.7}],
 [{code:'ShiftLeft',latin:'Shift',normal:'Shift',wide:2.1},...letters('ZXCVBNM','ᠽᠱᠴᠤᠪᠨᠮ'),{code:'Comma',latin:',',normal:'᠂',shift:'《'},{code:'Period',latin:'.',normal:'᠃',shift:'》'},{code:'Slash',latin:'/',normal:'·',shift:'︖'},{code:'ShiftRight',latin:'Shift',normal:'Shift',wide:2.6}],
 [{code:'Space',latin:'Space',normal:' ',wide:9}]
];
const shiftLetters:Record<string,string>={KeyQ:'ᡂ',KeyE:'ᠧ',KeyR:'ᠿ',KeyH:'ᠾ',KeyK:'ᠻ',KeyL:'ᡀ',KeyZ:'ᡁ',KeyC:'ᠼ',KeyN:'ᠩ'};
export const labels:Record<string,string>={'\u180b':'FVS1','\u180c':'FVS2','\u180d':'FVS3','\u180e':'MVS','\u202f':'NNBSP','\u200c':'ZWNJ','\u200d':'ZWJ',' ':'Зай','︔':';','︱':'|','︖':'?','︕':'!'};
export function keyOutput(k:Key,layout:KeyboardLayout,shifted=false,mongolianDigits=false){let value=k.normal;let s=k.shift||shiftLetters[k.code]||value;
 if(layout==='legacy'){if(k.code==='KeyQ'){value='ᠴ';s='ᠴ';}if(k.code==='KeyW'){value='ᠣ';s='ᠸ';}if(k.code==='KeyC'){value='ᠼ';s='ᡂ';}if(k.code==='Semicolon')value=';';if(k.code==='Slash'){value='.';s='?';}if(k.code==='BracketLeft')value='〔';if(k.code==='BracketRight')value='〕';if(k.code==='Digit1')s='!';if(k.code==='Digit4')s='—';if(k.code==='Backslash')s='|';}
 if(!shifted&&mongolianDigits&&/^Digit[0-9]$/.test(k.code))return String.fromCodePoint(0x1810+Number(k.code.slice(-1)));
 return shifted?s:value;
 }

export function keyHint(character:string,layout:KeyboardLayout,mongolianDigits=false):string|null{
 for(const shifted of [false,true]){
  const key=standard.flat().find(k=>!['Tab','CapsLock','Enter','Backspace','ShiftLeft','ShiftRight'].includes(k.code)&&keyOutput(k,layout,shifted,mongolianDigits)===character);
  if(key)return (shifted?'Shift + ':'')+key.latin;
 }
 return null;
}

type PhysicalKey={code:string;key?:string;shiftKey:boolean;ctrlKey:boolean;metaKey:boolean;altKey:boolean;isComposing:boolean};
export function physicalEdit(event:PhysicalKey,text:string,start:number,end:number,layout:KeyboardLayout,mongolianDigits=false):{text:string;caret:number}|null{
 if(event.isComposing||event.ctrlKey||event.metaKey||event.altKey)return null;
 if(/^Numpad[0-9]$/.test(event.code)&&event.key!==undefined&&!/^[0-9᠐-᠙]$/.test(event.key))return null;
 const code=/^Numpad[0-9]$/.test(event.code)?event.code.replace('Numpad','Digit'):event.code;
 const key=standard.flat().find(k=>k.code===code);
 if(!key||['Tab','CapsLock','Enter','ShiftLeft','ShiftRight'].includes(key.code))return null;
 if(key.code==='Backspace'){
  if(start===end){
   const before=Array.from(text.slice(0,start));
   start-=before.at(-1)?.length||0;
  }
  return {text:text.slice(0,start)+text.slice(end),caret:start};
 }
 const value=keyOutput(key,layout,event.shiftKey,mongolianDigits);
 return {text:text.slice(0,start)+value+text.slice(end),caret:start+value.length};
}
