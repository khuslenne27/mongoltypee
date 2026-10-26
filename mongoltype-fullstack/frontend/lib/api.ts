export type Language='mn-Cyrl'|'mn-Mong'|'en';
export type Mode='time'|'words';
export type Category='words'|'punctuation'|'numbers'|'mixed';
export type Config={language:Language;mode:Mode;category:Category;amount:number};
export type Test={id:string;text:string;demo:boolean;mode:Mode;category:Category;amount:number};
export type Result={id:number;language:Language;mode:Mode;category:Category;amount:number;demo:boolean;date:string;elapsed_ms:number;wpm:number;accuracy:number;errors:number;saved:boolean};
export function visitorId(){const key='mongoltype-visitor-v2';let id=localStorage.getItem(key);if(!id){id=crypto.randomUUID();localStorage.setItem(key,id);}return id;}
export async function api<T>(path:string,body?:unknown):Promise<T>{
 const response=await fetch('/api'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-Visitor-ID':visitorId()},body:body===undefined?undefined:JSON.stringify(body)});
 const type=response.headers.get('content-type')||'';
 if(!type.includes('application/json'))throw Error('Django backend холбогдсонгүй. backend серверээ асааж, setup_typing командыг ажиллуулна уу.');
 const data=await response.json();if(!response.ok)throw Error(data.detail||JSON.stringify(data));return data;
}
export const units=(s:string)=>Array.from(new Intl.Segmenter('mn',{granularity:'grapheme'}).segment(s.normalize('NFC')),x=>x.segment);
export function score(target:string,typed:string,ms:number){const expected=target.split(' '),actual=typed.split(' ');let correct=0,total=0;actual.forEach((word,i)=>{const a=units(word),b=units(expected[i]||'');correct+=a.filter((c,j)=>c===b[j]).length;total+=a.length;if(i<actual.length-1){total++;if(i<expected.length-1)correct++;}});return {wpm:ms?Math.round(correct/5/(Math.max(ms,100)/60000)*10)/10:0,accuracy:total?Math.round(correct/total*1000)/10:100,errors:total-correct};}
export function complete(target:string,typed:string){const a=target.split(' '),b=typed.split(' ');return b.length>a.length||(b.length===a.length&&units(b.at(-1)||'').length>=units(a.at(-1)||'').length);}
