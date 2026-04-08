import { computed, ref, watch } from 'vue';

export function usePagination(total: () => number, pageSize = 5) {
  const page = ref(1);
  const totalPages = computed(() => Math.max(1, Math.ceil(total() / pageSize)));

  watch(totalPages, (value) => {
    if (page.value > value) {
      page.value = value;
    }
  });

  const nextPage = () => {
    if (page.value < totalPages.value) {
      page.value += 1;
    }
  };

  const previousPage = () => {
    if (page.value > 1) {
      page.value -= 1;
    }
  };

  return {
    page,
    totalPages,
    nextPage,
    previousPage,
  };
}
