const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
export async function api(path:string, method="GET", body?:unknown) {
  const res = await fetch(base+path,{method,cache:"no-store",headers:body?{"Content-Type":"application/json"}:{},body:body?JSON.stringify(body):undefined});
  if (!res.ok) throw new Error((await res.json()).detail || "请求失败");
  return res.status===204 ? null : res.json();
}
export type Market = {country_code:string,country_name_zh:string,is_enabled:boolean};
export const statuses:Record<string,string> = {draft:"草稿",confirmed:"已确认",closed:"已关闭"};
export const categories:Record<string,string> = {packaging:"包装",logistics:"物流",insurance:"保险",other:"其他"};
export const money=(v:string)=>v.replace(/(\.\d*?[1-9])0+$|\.0+$/,"$1");
