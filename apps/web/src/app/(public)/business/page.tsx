import { PublicPage } from "@/features/public/public-page";
import { publicPages } from "@/lib/content/public-pages";

export default function BusinessPage() {
  return <PublicPage content={publicPages.business} />;
}
