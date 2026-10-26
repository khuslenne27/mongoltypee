import regex
import unicodedata
def units(text): return regex.findall(r'\X',unicodedata.normalize('NFC',text))
def score(target,typed,elapsed_ms):
    expected=target.split(' '); actual=typed.split(' '); correct=0; total=0
    for i,word in enumerate(actual):
        chars=units(word); wanted=units(expected[i]) if i<len(expected) else []
        correct+=sum(j<len(wanted) and c==wanted[j] for j,c in enumerate(chars))
        total+=len(chars)
        if i<len(actual)-1:
            total+=1
            if i<len(expected)-1: correct+=1
    return {'wpm':round(correct/5/(elapsed_ms/60000),1),'accuracy':round(correct/total*100,1) if total else 100,'errors':total-correct}
def completed(target,typed):
    expected=target.split(' '); actual=typed.split(' ')
    return len(actual)>len(expected) or (len(actual)==len(expected) and len(units(actual[-1]))>=len(units(expected[-1])))
