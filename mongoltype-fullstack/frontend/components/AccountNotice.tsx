'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {api,type AccountResponse} from '../lib/api';
export default function AccountNotice(){
 const [account,setAccount]=useState<AccountResponse|null>(null);
 useEffect(()=>{let alive=true;api<AccountResponse>('/auth/me').then(r=>{if(alive)setAccount(r);}).catch(()=>{});return()=>{alive=false;};},[]);
 if(!account)return null;
 return account.user?<p className="status-note">{account.user.username} · Нэвтэрсэн бүх төхөөрөмжийн үр дүн, ахиц.</p>:
  <p className="status-note">Зочны үр дүн энэ браузерт хамаарна. <Link href="/register" className="text-button">Бүртгүүлэх</Link> эсвэл <Link href="/login" className="text-button">нэвтрэх</Link> үед зочны үр дүн чинь бүртгэлд холбогдоно.</p>;
}
