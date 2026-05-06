import { PublicPage } from "@/features/public/public-page";
import { publicPagesExtra } from "@/lib/content/public-pages-extra";

export default function PricingPage() {
  return <PublicPage content={publicPagesExtra.pricing} />;
}
