export const controlLabels:Record<string,string>={
 '\u180b':'FVS1 — үсгийн хэлбэр сонгогч', '\u180c':'FVS2 — үсгийн хэлбэр сонгогч',
 '\u180d':'FVS3 — үсгийн хэлбэр сонгогч', '\u180e':'MVS — эгшиг тусгаарлагч',
 '\u202f':'NNBSP — нөхцөлийн нарийн зай', '\u200c':'ZWNJ — залгалт таслагч',
 '\u200d':'ZWJ — залгалт холбогч', ' ':'Зай',
};

export function clusterFeedback(expected:string, entered:string, last:boolean):'correct'|'pending'|'error'{
 if(expected===entered)return 'correct';
 // The final cluster may still receive a selector in the next input event.
 if(last&&entered&&expected.startsWith(entered)&&/^[\u180b-\u180d]+$/u.test(expected.slice(entered.length)))return 'pending';
 return 'error';
}

export function nextExpected(target:string, typed:string):string{
 const words=target.normalize('NFC').split(' '),parts=typed.normalize('NFC').split(' ');
 return Array.from((words[parts.length-1]||'').slice((parts.at(-1)||'').length))[0]||' ';
}
