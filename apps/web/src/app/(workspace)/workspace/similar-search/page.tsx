import { SimilarSearchWorkflow } from "@/features/workspace/similar-search-workflow";

export default function WorkspaceSimilarSearchPage() {
  return (
    <main className="px-6 py-8 lg:px-8 lg:py-10">
      <section className="site-card p-8 lg:p-10">
        <p className="eyebrow">Похожие товары</p>
        <h1 className="workspace-page-title mt-4">Поиск похожей одежды и альтернатив</h1>
        <p className="workspace-page-lead mt-4 max-w-[920px]">
          Загрузите фото вещи. Backend разберет одежду через Garment Identity Agent и сначала покажет релевантные товары из локального каталога магазинов.
        </p>
      </section>

      <section className="mt-[50px]">
        <SimilarSearchWorkflow />
      </section>
    </main>
  );
}
