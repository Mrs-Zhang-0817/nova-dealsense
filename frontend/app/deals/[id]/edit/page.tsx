import DealForm from "@/components/deal-form";
export default async function Page({params}:{params:Promise<{id:string}>}){return <DealForm id={(await params).id}/>}
