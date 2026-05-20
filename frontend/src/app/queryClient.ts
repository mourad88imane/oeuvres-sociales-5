/**
 * QUERY CLIENT — Configuration TanStack Query
 * Paramètres globaux : cache, retry, error handling.
 */
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Temps pendant lequel les données sont considérées fraîches
      staleTime: 1000 * 60 * 5,          // 5 minutes
      // Temps de conservation en cache après unmount
      gcTime: 1000 * 60 * 10,            // 10 minutes
      // Nombre de tentatives en cas d'erreur
      retry: (failureCount, error) => {
        // Pas de retry sur 401, 403, 404
        const status = (error as { response?: { status?: number } })?.response?.status;
        if (status && [401, 403, 404].includes(status)) return false;
        return failureCount < 2;
      },
      // Refetch au focus de la fenêtre
      refetchOnWindowFocus: true,
      // Refetch à la reconnexion réseau
      refetchOnReconnect: true,
    },
    mutations: {
      // Pas de retry automatique sur les mutations
      retry: false,
    },
  },
});
