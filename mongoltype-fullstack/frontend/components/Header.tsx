'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {api,type User,type AccountResponse} from '../lib/api';

export default function Header(){
 const path=usePathname();const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true);
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let alive=true;api<AccountResponse>('/auth/me').then(r=>{if(alive)setUser(r.user);})
  .catch(()=>{}).finally(()=>{if(alive)setLoading(false);});return()=>{alive=false;};},[path]);
 async function signOut(){setBusy(true);setError('');try{await api('/auth/logout',{});window.location.assign('/');}
  catch{setError('Гарах үйлдэл амжилтгүй. Дахин оролдоно уу.');setBusy(false);}}
 return <header className="site-header"><div className="header-inner">
  <Link href="/" className="logo"><span className="logo-mark">ᠪ</span>MONGOLTYPE</Link>
  <nav aria-label="Үндсэн цэс">{(user?[['/','Шалгалт'],['/profile','Профайл'],['/leaderboard','Чансаа']]:[['/','Шалгалт']]).map(([url,label])=><Link href={url} key={url} className={path===url?'active':''} aria-current={path===url?'page':undefined}>{label}</Link>)}</nav>
  {!loading&&<div className="header-auth">{user?<>
   <Link href="/profile" className="account"><span>{user.username}</span><b>{user.username.charAt(0).toUpperCase()}</b></Link>
   <button className="text-button" disabled={busy} onClick={()=>void signOut()}>{busy?'Гарч байна…':'Гарах'}</button>
  </>:<><Link href="/login">Нэвтрэх</Link><Link href="/register" className="primary-button">Бүртгүүлэх</Link></>}</div>}
 </div>{error&&<p role="alert" className="error-message header-auth-error">{error}</p>}</header>;
}
