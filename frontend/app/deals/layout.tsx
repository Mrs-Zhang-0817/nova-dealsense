import "./orders.css";
export default function Layout({children}:{children:React.ReactNode}){
 return <main className="orders"><header><a href="/">NOVA DealSense</a><a href="/deals">订单管理</a></header>{children}</main>;
}
