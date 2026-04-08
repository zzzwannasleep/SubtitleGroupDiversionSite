import { ref } from 'vue';
import { defineStore } from 'pinia';
import type { ReleaseQuery, ReleaseSort } from '@/types/release';

export const useReleaseFiltersStore = defineStore('releaseFilters', () => {
  const q = ref('');
  const category = ref('');
  const tag = ref('');
  const sort = ref<ReleaseSort>('latest');
  const page = ref(1);

  function hydrate(payload: ReleaseQuery) {
    q.value = payload.q ?? '';
    category.value = payload.category ?? '';
    tag.value = payload.tag ?? '';
    sort.value = payload.sort ?? 'latest';
    page.value = payload.page ?? 1;
  }

  function reset() {
    q.value = '';
    category.value = '';
    tag.value = '';
    sort.value = 'latest';
    page.value = 1;
  }

  function toQuery(): ReleaseQuery {
    return {
      q: q.value || undefined,
      category: category.value || undefined,
      tag: tag.value || undefined,
      sort: sort.value,
      page: page.value,
    };
  }

  return {
    q,
    category,
    tag,
    sort,
    page,
    hydrate,
    reset,
    toQuery,
  };
});

