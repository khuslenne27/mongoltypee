import {clusterFeedback} from './feedback';
export type Language='mn-Cyrl'|'mn-Mong'|'en';
export type Mode='time'|'words';
export type Category='words'|'punctuation'|'numbers'|'mixed';
export type Config={language:Language;mode:Mode;category:Category;amount:number};
export type Test={id:string;text:string;demo:boolean;corpus?:'reviewed'|'dictionary'|'demo';mode:Mode;category:Category;amount:number};
export type Result={id:number;language:Language;mode:Mode;category:Category;amount:number;demo:boolean;date:string;elapsed_ms:number;wpm:number;accuracy:number;errors:number;saved:boolean;rank_eligible:boolean;rank_reason:string};
export function visitorId(){const key='mongoltype-visitor-v2';let id=localStorage.getItem(key);if(!id){id=crypto.randomUUID();localStorage.setItem(key,id);}return id;}
let identityRequest:Promise<unknown>|null=null;
let csrfToken='';
export type User={id:number;username:string};
export type AccountResponse={user:User|null;csrf_token:string};
export async function api<T>(path:string,body?:unknown):Promise<T>{
 if(!identityRequest)identityRequest=(async()=>{await request('/auth/me');return request('/identity',{});})().catch(e=>{identityRequest=null;throw e;});
 await identityRequest;
 return request<T>(path,body);
}
async function request<T>(path:string,body?:unknown):Promise<T>{
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),10000);
 try{
 const cookieToken=document.cookie.split('; ').find(c=>c.startsWith('csrftoken='))?.slice('csrftoken='.length);
 const response=await fetch('/api'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',cache:'no-store',signal:controller.signal,headers:{'Content-Type':'application/json','X-Visitor-ID':visitorId(),'X-CSRFToken':cookieToken?decodeURIComponent(cookieToken):csrfToken},body:body===undefined?undefined:JSON.stringify(body)});
 const type=response.headers.get('content-type')||'';
 if(!type.includes('application/json'))throw Error(response.status===403?'Сессийн хамгаалалтын шалгалт амжилтгүй. Хуудсаа шинэчлээд дахин оролдоно уу.':'Django backend холбогдсонгүй. backend серверээ асааж, setup_typing командыг ажиллуулна уу.');
 const data=await response.json();if(data.csrf_token)csrfToken=data.csrf_token;if(!response.ok)throw Error([data.detail,...(Array.isArray(data.errors)?data.errors:[])].filter(Boolean).join(' ')||JSON.stringify(data));return data;
 }finally{clearTimeout(timer);}
}
export const units=(s:string)=>Array.from(new Intl.Segmenter('mn',{granularity:'grapheme'}).segment(s.normalize('NFC')),x=>x.segment);
export function score(target:string,typed:string,ms:number){const expected=target.split(' '),actual=typed.split(' ');let correct=0,total=0;actual.forEach((word,i)=>{const a=units(word),b=units(expected[i]||'');a.forEach((c,j)=>{const status=clusterFeedback(b[j]||'',c,i===actual.length-1&&j===a.length-1);if(status==='pending')return;total++;if(status==='correct')correct++;});if(i<actual.length-1){total++;if(i<expected.length-1)correct++;}});return {wpm:ms?Math.round(correct/5/(Math.max(ms,100)/60000)*10)/10:0,accuracy:total?Math.round(correct/total*1000)/10:100,errors:total-correct};}
export function complete(target:string,typed:string){const a=target.split(' '),b=typed.split(' ');return b.length>a.length||(b.length===a.length&&units(b.at(-1)||'').length>=units(a.at(-1)||'').length);}
