import {test} from 'node:test';
import assert from 'node:assert/strict';
import {api} from '../src/api/client.js';
globalThis.localStorage={getItem:()=>null};
test('post listing uses same origin API and encodes query',async()=>{
 let called;
 globalThis.fetch=async(url)=>{called=url;return {ok:true,json:async()=>({data:[]})}};
 assert.deepEqual(await api.listPosts({search:'hello world'}),{data:[]});
 assert.equal(called,'/api/posts?search=hello+world');
});
test('API errors reach caller',async()=>{
 globalThis.fetch=async()=>({ok:false,json:async()=>({error:'Access denied'})});
 await assert.rejects(api.listPosts(),/Access denied/);
});
test('authenticated creation uses bearer token',async()=>{
 globalThis.localStorage={getItem:()=> 'test-token'};
 let options;
 globalThis.fetch=async(url,opts)=>{options=opts;return {ok:true,json:async()=>({id:1})}};
 await api.createPost({title:'Test'});
 assert.equal(options.headers.Authorization,'Bearer test-token');
 assert.equal(options.method,'POST');
});
