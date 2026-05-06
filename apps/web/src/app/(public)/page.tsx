import { PublicPage } from "@/features/public/public-page";
import { publicPages } from "@/lib/content/public-pages";

export default function HomePage() {
  return <PublicPage content={publicPages.home} />;
}
