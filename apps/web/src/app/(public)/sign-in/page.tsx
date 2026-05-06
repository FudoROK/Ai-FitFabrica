import { VisualPlaceholder } from "@/components/ui/visual-placeholder";
import { SignInForm } from "@/features/public/sign-in-form";

export default function SignInPage() {
  return (
    <main className="public-page">
      <section className="page-shell auth-layout">
        <SignInForm />
        <VisualPlaceholder
          data={{
            eyebrow: "Access Placeholder",
            title: "Зона для будущего access preview",
            body: "Позже сюда можно вставить защищенный workspace overview, identity state или enterprise access diagram.",
            items: ["Auth state", "Protected routes", "Workspace preview", "Role checks"]
          }}
        />
      </section>
    </main>
  );
}
