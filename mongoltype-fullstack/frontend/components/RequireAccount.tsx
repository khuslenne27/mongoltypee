'use client';
import {useEffect,useState,type ReactNode} from 'react';
import {api,type AccountResponse} from '../lib/api';

export default function RequireAccount({children}:{children:ReactNode}){
 const [allowed,setAllowed]=useState(false),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 useEffect(()=>{
  let alive=true;setError('');
  api<AccountResponse>('/auth/me').then(result=>{
   if(!alive)return;
   if(!result.user){window.location.replace('/login');return;}
   setAllowed(true);
  }).catch(()=>{if(alive)setError('Нэвтрэх төлөвийг шалгаж чадсангүй.');});
  return()=>{alive=false;};
 },[retry]);
 if(!allowed)return <main className="profile-page">{error?<p role="alert">{error} <button className="text-button" onClick={()=>setRetry(n=>n+1)}>Дахин оролдох</button></p>:<p role="status">Нэвтрэх төлөвийг шалгаж байна…</p>}</main>;
 return children;
}
