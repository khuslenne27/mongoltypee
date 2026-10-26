'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
export default function Header(){const path=usePathname();return <header className="site-header"><div className="header-inner"><Link href="/" className="logo"><span className="logo-mark">ᠪ</span>MONGOLTYPE</Link><nav aria-label="Үндсэн цэс">{[['/','Шалгалт'],['/profile','Профайл'],['/leaderboard','Чансаа']].map(([url,label])=><Link href={url} key={url} className={path===url?'active':''} aria-current={path===url?'page':undefined}>{label}</Link>)}</nav><Link href="/profile" className="account"><span>Миний профайл</span><b>Б</b></Link></div></header>}
