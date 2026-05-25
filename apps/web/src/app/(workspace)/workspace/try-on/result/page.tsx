import { Suspense } from "react";
import { TryOnResultView } from "@/features/workspace/try-on-result";

export default function WorkspaceTryOnResultPage() {
  return (
    <Suspense fallback={<main className="px-8 py-10 lg:px-16">Загружаем результат Try-On...</main>}>
      <TryOnResultView />
    </Suspense>
  );
}
