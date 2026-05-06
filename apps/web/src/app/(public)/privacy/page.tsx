import { PublicPage } from "@/features/public/public-page";
import { publicPagesExtra } from "@/lib/content/public-pages-extra";

export default function PrivacyPage() {
  return <PublicPage content={publicPagesExtra.privacy} />;
}
