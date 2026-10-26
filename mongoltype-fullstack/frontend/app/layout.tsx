import type {Metadata} from 'next';
import '@fontsource/noto-sans-mongolian/400.css';
import './globals.css';
import Header from '../components/Header';
export const metadata:Metadata={title:'MONGOLTYPE — Бичих хурдаа сорь',description:'Монгол кирилл, үндэсний босоо бичиг болон англиар бичих хурдаа шалгаарай.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="mn"><body><Header/>{children}</body></html>}
