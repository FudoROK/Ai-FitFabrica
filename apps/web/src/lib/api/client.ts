import { AdminBusinessCatalogApiClient } from "@/lib/api/clients/admin-business-catalog-client";
import { AdminTaxonomyApiClient } from "@/lib/api/clients/admin-taxonomy-client";
import { BusinessCatalogApiClient } from "@/lib/api/clients/business-catalog-client";
import { PublicApiClient } from "@/lib/api/clients/public-client";
import { TryOnApiClient } from "@/lib/api/clients/try-on-client";
import { WorkspaceCommerceApiClient } from "@/lib/api/clients/workspace-commerce-client";
import { WorkspaceApiClient } from "@/lib/api/clients/workspace-client";

export type WebApiClient = PublicApiClient &
  TryOnApiClient &
  WorkspaceApiClient &
  BusinessCatalogApiClient &
  AdminBusinessCatalogApiClient &
  WorkspaceCommerceApiClient &
  AdminTaxonomyApiClient;

type DomainClient =
  | PublicApiClient
  | TryOnApiClient
  | WorkspaceApiClient
  | BusinessCatalogApiClient
  | AdminBusinessCatalogApiClient
  | WorkspaceCommerceApiClient
  | AdminTaxonomyApiClient;

type WebApiClientConstructor = {
  new (baseUrl: string): WebApiClient;
};

class WebApiClientFacade {
  public constructor(baseUrl: string) {
    attachClientMethods(this, [
      new PublicApiClient(baseUrl),
      new TryOnApiClient(baseUrl),
      new WorkspaceApiClient(baseUrl),
      new BusinessCatalogApiClient(baseUrl),
      new AdminBusinessCatalogApiClient(baseUrl),
      new WorkspaceCommerceApiClient(baseUrl),
      new AdminTaxonomyApiClient(baseUrl),
    ]);
  }
}

export const WebApiClient = WebApiClientFacade as WebApiClientConstructor;

function attachClientMethods(target: object, clients: DomainClient[]): void {
  for (const client of clients) {
    const prototype = Object.getPrototypeOf(client) as object;

    for (const propertyName of Object.getOwnPropertyNames(prototype)) {
      if (propertyName === "constructor") {
        continue;
      }

      const descriptor = Object.getOwnPropertyDescriptor(prototype, propertyName);
      if (!descriptor || typeof descriptor.value !== "function") {
        continue;
      }

      Object.defineProperty(target, propertyName, {
        configurable: true,
        enumerable: false,
        value: descriptor.value.bind(client) as unknown,
      });
    }
  }
}
