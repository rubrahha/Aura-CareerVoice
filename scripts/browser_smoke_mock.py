"""Browser integration smoke check with mocked network (localhost restricted in test sandbox).
Run: python tests/test_browser_mock.py
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT/'app/static/index.html').read_text()
CSS = (ROOT/'app/static/styles.css').read_text()
JS = (ROOT/'app/static/app.js').read_text()
with TestClient(app) as client:
    HEALTH = client.get('/api/health').json()
    TOPICS = client.get('/api/topics').json()
    def payload_for(text):
        return client.post('/api/chat/stream',json={'message':text,'history':[],'profile':{}}).text
    STREAMS = {q:payload_for(q) for q in [
        'How do I become an AI engineer? Give me a beginner roadmap.',
        'Interested in design.',
        'I want to be a product manager',
        "I completed BCA and don't enjoy heavy coding. Which careers should I explore?"
    ]}

def init(page):
    page.set_content(HTML.replace('<link rel="stylesheet" href="/static/styles.css">','').replace('<script src="/static/app.js" defer></script>',''))
    page.add_style_tag(content=CSS)
    # about:blank is an opaque origin; stub browser sessionStorage for isolated UI checks.
    page.evaluate("""() => { const mem=new Map(); Object.defineProperty(window,'sessionStorage',{configurable:true,value:{getItem(k){return mem.has(k)?mem.get(k):null},setItem(k,v){mem.set(k,String(v))},removeItem(k){mem.delete(k)}}}); }""")
    page.evaluate('''([health,topics,streams]) => {
      const originalFetch = window.fetch.bind(window);
      window.fetch = async (url,opts) => {
        const path=String(url);
        if (path==='/api/health') return new Response(JSON.stringify(health),{status:200,headers:{'Content-Type':'application/json'}});
        if (path==='/api/topics') return new Response(JSON.stringify(topics),{status:200,headers:{'Content-Type':'application/json'}});
        if (path==='/api/chat/stream') {
          const question=JSON.parse(opts.body).message;
          const body=streams[question] || streams[Object.keys(streams)[0]];
          const encoder=new TextEncoder(); let offset=0;
          const stream=new ReadableStream({async pull(controller){
            if(window.__slowStream) await new Promise(resolve=>setTimeout(resolve,28));
            if (opts.signal.aborted) {controller.error(new DOMException('Aborted','AbortError'));return;}
            if (offset>=body.length){controller.close();return;}
            const end=Math.min(offset+28,body.length);
            controller.enqueue(encoder.encode(body.slice(offset,end)));offset=end;
          }});
          return new Response(stream,{status:200,headers:{'Content-Type':'text/event-stream'}});
        }
        return originalFetch(url,opts);
      };
    }''',[HEALTH,TOPICS,STREAMS])
    page.add_script_tag(content=JS)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    desktop=browser.new_page(viewport={'width':1440,'height':900})
    errors=[];desktop.on('pageerror',lambda error: errors.append(str(error)))
    init(desktop)
    desktop.screenshot(path=str(ROOT/'previews'/'welcome_desktop.png'),full_page=True)
    desktop.get_by_role('button',name='Roadmap to AI engineer').click()
    desktop.locator('.message.assistant .message-actions .mini-action').first.wait_for(timeout=10000)
    assert desktop.locator('.message.assistant .message-bubble').last.inner_text().strip()
    desktop.screenshot(path=str(ROOT/'previews'/'desktop_chat.png'),full_page=True)
    desktop.get_by_role('button',name='View retrieved career sources').click()
    assert desktop.locator('.inline-sources:not([hidden])').count() == 1
    desktop.locator('#newChatButton').click()
    assert desktop.locator('.message').count()==0
    desktop.locator('#messageInput').fill('Interested in design.')
    desktop.locator('#messageInput').press('Enter')
    desktop.locator('.message.assistant .message-actions .mini-action').first.wait_for(timeout=10000)
    desktop.locator('#profileButton').click()
    desktop.locator('#profile-education').fill('BCA')
    desktop.get_by_role('button',name='Save profile').click()
    # Mock transcription API; real physical-microphone permission is a separate external check.
    desktop.evaluate('''() => {
      Object.defineProperty(window,'isSecureContext',{configurable:true,value:true});
      window.SpeechRecognition = window.webkitSpeechRecognition = class {
        start(){setTimeout(()=>{
          this.onstart?.();
          this.onresult?.({results:[{0:{transcript:'I want to be a product manager'},isFinal:true}]});
          this.onend?.();
        },20);}
        abort(){}
      };
    }''')
    desktop.locator('#micButton').click()
    desktop.get_by_text('I want to be a product manager',exact=True).wait_for(timeout=8000)
    desktop.wait_for_function("document.querySelector('#stopButton').hidden && document.querySelectorAll('.message.assistant').length===2",timeout=8000)
    # Stop button should interrupt an in-progress streamed response.
    desktop.evaluate('window.__slowStream = true')
    desktop.locator('#messageInput').fill('I want to be a product manager')
    desktop.locator('#messageInput').press('Enter')
    desktop.locator('#stopButton').wait_for(state='visible',timeout=4000)
    desktop.locator('#stopButton').click()
    desktop.locator('#stopButton').wait_for(state='hidden',timeout=4000)
    assert not errors, errors
    print('DESKTOP PASS: streamed text, sources, new chat, typed question, modal; no JS errors')
    mobile=browser.new_page(viewport={'width':375,'height':812},is_mobile=True,has_touch=True)
    mobile_errors=[];mobile.on('pageerror',lambda e: mobile_errors.append(str(e)))
    init(mobile)
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth')
    mobile.get_by_role('button',name='Open menu').click()
    assert 'open' in mobile.locator('#sidebar').get_attribute('class')
    mobile.locator('#profileButton').click()
    mobile.locator('#profile-interests').fill('Art')
    mobile.get_by_role('button',name='Save profile').click()
    mobile.get_by_role('button',name="I don't like heavy coding").click()
    mobile.locator('.message.assistant .message-actions .mini-action').first.wait_for(timeout=10000)
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth')
    mobile.evaluate("document.querySelector('#chatScroll').scrollTop = 0")
    mobile.wait_for_timeout(4700)  # prevent transient toast obscuring the mobile screenshot
    mobile.screenshot(path=str(ROOT/'previews'/'mobile_chat.png'),full_page=True)
    assert not mobile_errors,mobile_errors
    print('MOBILE PASS: menus, profile, streamed answer, zero horizontal overflow; no JS errors')
    browser.close()
