'use client';
import {useEffect,useState,type FormEvent} from 'react';
import Link from 'next/link';
import {api,type AccountResponse} from '../lib/api';

export default function AuthForm({register=false}:{register?:boolean}){
 const [username,setUsername]=useState(''),[password,setPassword]=useState(''),[confirm,setConfirm]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[show,setShow]=useState(false);
 useEffect(()=>{api<AccountResponse>('/auth/me').then(r=>{if(r.user)window.location.replace('/profile');}).catch(()=>{});},[]);
 async function submit(event:FormEvent<HTMLFormElement>){
  event.preventDefault();if(busy)return;setError('');
  if(register&&password!==confirm){setError('Нууц үгийн давталт таарахгүй байна.');return;}
  setBusy(true);
  try{await api<AccountResponse>(register?'/auth/register':'/auth/login',{username,password});window.location.assign('/profile');}
  catch(e){setError(e instanceof Error?e.message:'Дахин оролдоно уу.');setBusy(false);}
 }
 return <main className="auth-page"><section className="auth-card">
  <div className="eyebrow">MONGOLTYPE</div><h1>{register?'Бүртгэл үүсгэх':'Нэвтрэх'}</h1>
  <p className="status-note">Үр дүн, ахицаа бүртгэлдээ хадгалаад өөр төхөөрөмжөөс үргэлжлүүлээрэй.</p>
  <form onSubmit={submit}>
   <label htmlFor="username">Нэвтрэх нэр</label><input id="username" name="username" value={username} onChange={e=>setUsername(e.target.value)} required maxLength={150} autoComplete="username" autoCapitalize="none" spellCheck={false} disabled={busy}/>
   {register&&<small>Үсэг, тоо болон @ . + - _ ашиглаж болно. Нэвтрэх нэр чинь чансаанд харагдана.</small>}
   <label htmlFor="password">Нууц үг</label><input id="password" name="password" type={show?'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} required minLength={register?8:undefined} maxLength={256} autoComplete={register?'new-password':'current-password'} disabled={busy}/>
   {register&&<><small>8-аас доошгүй тэмдэгттэй, түгээмэл бус, зөвхөн тооноос бүрдээгүй нууц үг сонгоорой.</small>
    <label htmlFor="confirm">Нууц үгээ давтах</label><input id="confirm" name="confirm" type={show?'text':'password'} value={confirm} onChange={e=>setConfirm(e.target.value)} required autoComplete="new-password" disabled={busy}/></>}
   <label className="password-toggle"><input type="checkbox" checked={show} onChange={e=>setShow(e.target.checked)}/> Нууц үг харуулах</label>
   {error&&<p role="alert" className="error-message">{error}</p>}
   <button className="primary-button" disabled={busy}>{busy?'Түр хүлээнэ үү…':register?'Бүртгүүлэх':'Нэвтрэх'}</button>
  </form>
  <p className="auth-switch">{register?'Бүртгэлтэй юу?':'Бүртгэлгүй юу?'} <Link href={register?'/login':'/register'}>{register?'Нэвтрэх':'Бүртгүүлэх'}</Link></p>
  <p className="status-note">Энэ браузерийн зочин шалгалтууд нэвтрэх үед бүртгэлд чинь холбогдоно.</p>
  <Link href="/" className="text-button">Зочноор үргэлжлүүлэх</Link>
 </section></main>;
}
