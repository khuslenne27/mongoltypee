'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import AccountNotice from '../../components/AccountNotice';
import RequireAccount from '../../components/RequireAccount';
import {api,type Result,type Config} from '../../lib/api';

type Settings=Config&{demo:boolean};
type Group=Settings&{count:number;best_wpm:number};
type Mistake={text:string;count:number};
type Progress={groups:Group[];selected:Settings|null;summary:{count:number;average_wpm:number|null;average_accuracy:number|null;best:Result|null;latest_delta:number|null}|null;recent:Result[];history:Result[];letters:Mistake[];words:Mistake[];comparison:{current:number;previous:number;delta:number}|null};
const languages:Record<string,string>={'mn-Mong':'Монгол бичиг','mn-Cyrl':'Кирилл',en:'English'};
const categories:Record<string,string>={words:'Энгийн үг',punctuation:'Цэг, тэмдэгт',numbers:'Тоо',mixed:'Холимог'};
const key=(s:Settings)=>new URLSearchParams({language:s.language,mode:s.mode,category:s.category,amount:String(s.amount),demo:String(s.demo)}).toString();
const label=(s:Settings)=>`${languages[s.language]} · ${s.amount} ${s.mode==='time'?'сек':'үг'} · ${categories[s.category]} · ${s.demo?'Толь / туршилт':'Хянагдсан сан'}`;
const delta=(n:number)=>`${n>0?'+':''}${n.toFixed(1)} WPM`;
const controlNames:Record<string,string>={'\u180b':'FVS1','\u180c':'FVS2','\u180d':'FVS3','\u180e':'MVS','\u180f':'FVS4','\u202f':'NNBSP','\u200c':'ZWNJ','\u200d':'ZWJ'};
const readable=(s:string)=>Array.from(s,c=>controlNames[c]?` [${controlNames[c]}] `:c).join('');

export default function Profile(){
 return <RequireAccount><ProfileContent/></RequireAccount>;
}
function ProfileContent(){
 const [data,setData]=useState<Progress|null>(null),[selection,setSelection]=useState('');
 const [loading,setLoading]=useState(true),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 useEffect(()=>{
  let alive=true;setLoading(true);setError('');
  api<Progress>('/progress'+(selection?'?'+selection:'')).then(result=>{if(alive)setData(result);})
   .catch(e=>{if(alive)setError(e.message);}).finally(()=>{if(alive)setLoading(false);});
  return()=>{alive=false;};
 },[selection,retry]);
 const stats=data?.summary,best=stats?.best,vertical=data?.selected?.language==='mn-Mong';
 const graph=data?.recent||[],maximum=Math.max(10,...graph.map(r=>r.wpm));
 const points=graph.map((r,i)=>({x:40+i*720/Math.max(1,graph.length-1),y:145-r.wpm/maximum*110,result:r}));
 function mistakes(title:string,rows:Mistake[]){
  return <section className="chart-card mistake-card"><h2>{title}</h2>
   {!rows.length?<p className="status-note">Энэ тохиргоонд хадгалагдсан алдаа алга.</p>:<ol className="mistake-list">{rows.map(row=><li key={row.text}>
    <span className={vertical?'mistake-script':''} lang={vertical?'mn-Mong':undefined}>{readable(row.text)}</span><strong>{row.count} удаа</strong>
   </li>)}</ol>}
  </section>;
 }
 return <main className="profile-page">
  <div className="profile-heading"><div className="eyebrow">МИНИЙ АХИЦ</div></div>
  <section className="profile-banner"><div className="large-avatar">Б</div><div className="profile-identity">
   <h1>Бичилтийн ахиц</h1><p>Ижил тохиргооны үр дүнгээ харьцуулаарай.</p><small>Хадгалсан шалгалтын түүх</small>
  </div></section>
  <AccountNotice/>
  {!!data?.groups.length&&<div className="filter-row progress-filter"><label htmlFor="progress-setting">Харьцуулах тохиргоо</label>
   <select id="progress-setting" value={selection||(data.selected?key(data.selected):'')} onChange={e=>setSelection(e.target.value)}>
    {data.groups.map(group=><option key={key(group)} value={key(group)}>{label(group)} · {group.count} шалгалт</option>)}
   </select></div>}
  {loading&&<p role="status">Ахицын мэдээллийг ачаалж байна…</p>}
  {error&&<div role="alert" className="error-message">{error} <button className="text-button" onClick={()=>setRetry(n=>n+1)}>Дахин оролдох</button></div>}
  {!loading&&!error&&(!stats?.count)?<div className="profile-empty">Одоогоор үр дүн алга.<br/><Link href="/" className="primary-button">Шалгалт эхлүүлэх</Link></div>:null}
  {!loading&&!error&&!!stats?.count&&<>
   <p className="status-note">Хэл, хугацаа/үгийн тоо, ангилал, сангийн төрөл ижил шалгалтуудыг харьцуулж байна. Статистик бүх тохирох үр дүнг хамарна.</p>
   <div className="summary-grid">{[
    ['ХУВИЙН ДЭЭД АМЖИЛТ',`${best?.wpm??'—'} WPM`],['ДУНДАЖ ХУРД',`${stats.average_wpm} WPM`],
    ['ДУНДАЖ НАРИЙВЧЛАЛ',`${stats.average_accuracy}%`],['НИЙТ ШАЛГАЛТ',String(stats.count)],
   ].map(([name,value])=><div className="summary-card" key={name}><span>{name}</span><strong>{value}</strong></div>)}</div>
   <div className="progress-comparisons">
    <section className="chart-card"><h2>Өмнөх шалгалттай харьцуулахад</h2><strong className="progress-value">{stats.latest_delta===null?'—':delta(stats.latest_delta)}</strong>
     <p className="status-note">{stats.latest_delta===null?'Харьцуулахын тулд энэ тохиргоогоор дахин нэг шалгалт өгөөрэй.':'Хамгийн сүүлийн хоёр шалгалтын хурдны зөрүү.'}</p>
    </section>
    <section className="chart-card"><h2>Сүүлийн 5 / өмнөх 5</h2><strong className="progress-value">{data?.comparison?delta(data.comparison.delta):'—'}</strong>
     <p className="status-note">{data?.comparison?`${data.comparison.current} WPM / ${data.comparison.previous} WPM дундаж хурд`:`Харьцуулалт хийхэд 10 шалгалт хэрэгтэй (${stats.count}/10).`}</p>
    </section>
   </div>
   {best&&<p className="status-note">Хувийн дээд амжилт: {new Date(best.date).toLocaleString('mn-MN')} · {best.accuracy}% нарийвчлал · Энэ тохиргооны бүх хугацааны үр дүнгээс.</p>}
   <section className="chart-card"><h2>Сүүлийн 10 шалгалтын хурд</h2>
    <svg viewBox="0 0 800 190" role="img" aria-label="Ижил тохиргооны сүүлийн 10 шалгалтын WPM график">
     <line x1="40" x2="760" y1="145" y2="145" stroke="#e8e1d6"/>
     <polyline fill="none" stroke="#183f35" strokeWidth="2" points={points.map(p=>`${p.x},${p.y}`).join(' ')}/>
     {points.map(p=><g key={p.result.id}><circle cx={p.x} cy={p.y} r="4" fill="#b9974e"><title>{p.result.wpm} WPM · {new Date(p.result.date).toLocaleString('mn-MN')}</title></circle>
      <text x={p.x} y="175" textAnchor="middle" fontSize="12" fill="#183f35">{p.result.wpm}</text></g>)}
    </svg>
   </section>
   <p className="status-note">Алдааны шинжилгээ нь эцэст хадгалсан бичвэрт тулгуурлана. Засаж арилгасан алдааг тоолохгүй; хугацаа дуусахад бичиж амжаагүй хэсгийг алдаа гэж үзэхгүй. Үсэг нь бичих ёстой байсан тэмдэгтийг харуулна.</p>
   <div className="progress-comparisons">{mistakes('Хамгийн их алддаг үсэг / тэмдэгт',data?.letters||[])}{mistakes('Хамгийн их алддаг үг',data?.words||[])}</div>
   <div className="history-table"><table><caption>Энэ тохиргооны сүүлийн 50 шалгалт</caption><thead><tr><th>ОГНОО</th><th>ХУРД</th><th>НАРИЙВЧЛАЛ</th><th>АЛДАА</th></tr></thead>
    <tbody>{data?.history.map(r=><tr key={r.id}><td>{new Date(r.date).toLocaleString('mn-MN')}</td><td>{r.wpm} WPM{r.id===best?.id?' ★':''}</td><td>{r.accuracy}%</td><td>{r.errors}</td></tr>)}</tbody>
   </table></div>
  </>}
 </main>;
}
