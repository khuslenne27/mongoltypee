'use client';
import {useCallback,useEffect,useLayoutEffect,useRef,useState} from 'react';
import {units} from '../lib/api';
type Props={target:string;typed:string;vertical:boolean;disabled:boolean;onChange:(s:string,composing:boolean)=>void;inputRef:React.RefObject<HTMLTextAreaElement|null>};
export default function TypingViewport({target,typed,vertical,disabled,onChange,inputRef}:Props){
 const viewport=useRef<HTMLDivElement>(null),flow=useRef<HTMLDivElement>(null),wordRefs=useRef<(HTMLSpanElement|null)[]>([]),composition=useRef(false);
 const [caret,setCaret]=useState({left:0,top:0,width:2,height:34});
 const [glyphs,setGlyphs]=useState<{top:number;bottom:number;correct:boolean}[]>([]);
 const words=target.split(' '),parts=typed.normalize('NFC').split(' '),active=Math.min(parts.length-1,words.length-1),current=parts[active]||'';
 const place=useCallback(()=>{const vp=viewport.current,content=flow.current,word=wordRefs.current[active];if(!vp||!content||!word)return;
  let range=document.createRange();let rect:DOMRect;const clusters=units(words[active]||'');const at=Math.min(units(current).length,clusters.length);
  if(vertical){const node=word.firstChild;if(!node)return;
   const wordBox=word.getBoundingClientRect(),entered=units(current);let cursorOffset=0;const marks:{top:number;bottom:number;correct:boolean}[]=[];
   clusters.forEach((cluster,j)=>{if(j<entered.length){const highlight=document.createRange();highlight.setStart(node,cursorOffset);highlight.setEnd(node,cursorOffset+cluster.length);const box=highlight.getBoundingClientRect();marks.push({top:Math.max(0,box.top-wordBox.top),bottom:Math.max(0,wordBox.bottom-box.bottom),correct:entered[j]===cluster});}cursorOffset+=cluster.length;});setGlyphs(marks);
const offset=clusters.slice(0,at).join('').length;range.setStart(node,Math.min(offset,node.textContent?.length||0));range.collapse(true);rect=range.getBoundingClientRect();
   if(rect.height===0&&rect.width===0){const from=Math.max(0,offset-1);range.setStart(node,from);range.setEnd(node,Math.min(from+1,node.textContent?.length||0));const r=range.getBoundingClientRect();rect=new DOMRect(r.left,at?r.bottom:r.top,r.width,0);}
  }else{const char=word.querySelector(`[data-char="${at}"]`) as HTMLElement|null;rect=char?char.getBoundingClientRect():word.getBoundingClientRect();if(!char)rect=new DOMRect(rect.right,rect.top,0,rect.height);}
  const bounds=vp.getBoundingClientRect(),base=content.getBoundingClientRect(),line=Number.parseFloat(getComputedStyle(content).lineHeight);
  // Text DOM and order stay fixed. Only the viewport moves at a line/column boundary.
  if(vertical){const origin=wordRefs.current[0]?.getBoundingClientRect().left??base.left;const column=Math.max(0,Math.round((word.getBoundingClientRect().left-origin)/line));const left=rect.left-bounds.left+vp.scrollLeft;const top=rect.top-bounds.top+vp.scrollTop;setCaret({left,top,width:Math.max(28,rect.width),height:2});vp.scrollLeft=column*line;vp.scrollTop=0;}
  else{const row=Math.max(0,Math.floor((rect.top-base.top+line*.15)/line));const left=rect.left-bounds.left+vp.scrollLeft;const top=rect.top-bounds.top+vp.scrollTop;setCaret({left,top,width:2,height:Math.min(36,rect.height||36)});vp.scrollTop=row*line;vp.scrollLeft=0;}
 },[active,current,target,vertical]);
 useLayoutEffect(()=>{place();},[place]);
 useEffect(()=>{const resize=new ResizeObserver(()=>place());if(viewport.current)resize.observe(viewport.current);let alive=true;document.fonts.ready.then(()=>{if(alive)place();});return()=>{alive=false;resize.disconnect();};},[place]);
 return <div className="typing-shell"><div ref={viewport} className={`reading-viewport ${vertical?'mongolian-viewport':''}`} onClick={()=>inputRef.current?.focus()}><div ref={flow} className={`reading-flow ${vertical?'mongolian-flow':''}`} lang={vertical?'mn-Mong':undefined}>{words.map((word,i)=><span key={`${target.slice(0,20)}-${i}`} className={`stable-word ${i<active?(parts[i]===word?'word-correct':'word-error'):i===active?'active-word':''}`} ref={el=>{wordRefs.current[i]=el;}}>{vertical?<>{word}{i===active&&glyphs.map((glyph,j)=><span key={j} aria-hidden="true" className={`glyph-overlay ${glyph.correct?'glyph-correct':'glyph-error'}`} style={{clipPath:`inset(${glyph.top}px 0 ${glyph.bottom}px 0)`}}>{word}</span>)}</>:units(word).map((char,j)=><span data-char={j} key={j} className={i===active&&j<units(current).length?(units(current)[j]===char?'letter-correct':'letter-error'):''}>{char}</span>)}</span>)}</div><span className={`tracking-caret ${vertical?'horizontal-caret':''}`} style={caret} aria-hidden="true"/></div>
 <label htmlFor="typing-input" className="sr-only">Дээрх эхийг хуулж бичих</label><textarea ref={inputRef} id="typing-input" className="capture-input" value={typed} disabled={disabled} spellCheck={false} autoCorrect="off" autoComplete="off" autoCapitalize="off" onChange={e=>onChange(e.target.value,composition.current)} onCompositionStart={()=>{composition.current=true;}} onCompositionEnd={e=>{composition.current=false;onChange(e.currentTarget.value,false);}} onPaste={e=>e.preventDefault()} onDrop={e=>e.preventDefault()} onKeyDown={e=>{if(e.key==='Enter'&&!e.nativeEvent.isComposing)e.preventDefault();}}/>
 </div>
}
