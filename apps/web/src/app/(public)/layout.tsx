import { PublicFooter } from "@/components/navigation/public-footer";
import { PublicHeader } from "@/components/navigation/public-header";

export default function PublicLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="site-page">
      <PublicHeader />
      {children}
      <PublicFooter />
    </div>
  );
}
