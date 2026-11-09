import "../styles/global.css";
export const metadata = { title: "NOVA DealSense" };
export default function Layout({children}: {children: React.ReactNode}) {
  return <html lang="zh-CN"><body>{children}</body></html>;
}
