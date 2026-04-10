<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import AppAlert from '@/components/app/AppAlert.vue';
import AppCard from '@/components/app/AppCard.vue';
import AppEmpty from '@/components/app/AppEmpty.vue';
import AppLoading from '@/components/app/AppLoading.vue';
import AppPageHeader from '@/components/app/AppPageHeader.vue';
import UiButton from '@/components/ui/UiButton.vue';
import UiInput from '@/components/ui/UiInput.vue';
import UiSelect from '@/components/ui/UiSelect.vue';
import UiTable from '@/components/ui/UiTable.vue';
import { createInviteCodes, listInviteCodes, revokeInviteCode } from '@/services/admin';
import type { InviteCode, InviteCodeStatus } from '@/types/admin';
import { formatDateTime } from '@/utils/format';

const inviteCodes = ref<InviteCode[]>([]);
const loading = ref(true);
const creating = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const copiedCode = ref('');
const latestCreatedCodes = ref<InviteCode[]>([]);

const form = reactive({
  count: '1',
  note: '',
  expiresAt: '',
});

const summaryCards = computed(() => [
  {
    label: '全部邀请码',
    value: inviteCodes.value.length,
    hint: '包含可用、已使用、已过期和已停用的邀请码。',
  },
  {
    label: '可立即使用',
    value: inviteCodes.value.filter((item) => item.status === 'available').length,
    hint: '当前还能发给成员注册的单次邀请码。',
  },
  {
    label: '已完成注册',
    value: inviteCodes.value.filter((item) => item.status === 'used').length,
    hint: '已经被成员消耗并完成注册的邀请码。',
  },
  {
    label: '已失效',
    value: inviteCodes.value.filter((item) => item.status === 'expired' || item.status === 'revoked').length,
    hint: '过期或被管理员手动停用的邀请码。',
  },
]);

function statusLabel(status: InviteCodeStatus) {
  const map: Record<InviteCodeStatus, string> = {
    available: '可用',
    used: '已使用',
    expired: '已过期',
    revoked: '已停用',
  };
  return map[status];
}

function statusClasses(status: InviteCodeStatus) {
  const map: Record<InviteCodeStatus, string> = {
    available: 'bg-green-100 text-green-700',
    used: 'bg-blue-100 text-blue-700',
    expired: 'bg-amber-100 text-amber-700',
    revoked: 'bg-slate-200 text-slate-700',
  };
  return map[status];
}

function formatOptionalDateTime(value: string | null) {
  return value ? formatDateTime(value) : '未设置';
}

function resetForm() {
  form.count = '1';
  form.note = '';
  form.expiresAt = '';
}

function serializeExpiresAt(value: string) {
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString();
}

async function loadData() {
  loading.value = true;
  errorMessage.value = '';

  try {
    inviteCodes.value = await listInviteCodes();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '邀请码列表加载失败。';
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  feedback.value = '';
  errorMessage.value = '';
  creating.value = true;

  try {
    const created = await createInviteCodes({
      count: Number(form.count),
      note: form.note.trim() || undefined,
      expiresAt: serializeExpiresAt(form.expiresAt),
    });
    latestCreatedCodes.value = created;
    feedback.value = `已生成 ${created.length} 个邀请码。`;
    resetForm();
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '生成邀请码失败。';
  } finally {
    creating.value = false;
  }
}

async function handleRevoke(item: InviteCode) {
  feedback.value = '';
  errorMessage.value = '';

  try {
    await revokeInviteCode(item.id);
    feedback.value = `邀请码 ${item.code} 已停用。`;
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '停用邀请码失败。';
  }
}

async function copyCode(code: string) {
  try {
    if (!navigator?.clipboard) {
      throw new Error('clipboard-unavailable');
    }
    await navigator.clipboard.writeText(code);
    copiedCode.value = code;
    feedback.value = `邀请码 ${code} 已复制。`;
  } catch {
    errorMessage.value = '复制失败，请手动复制邀请码。';
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader
    title="邀请码管理"
    description="关闭公开注册后，站点会自动切换为邀请码注册。这里可以批量生成、查看使用情况并停用未使用的邀请码。"
  >
    <template #actions>
      <UiButton variant="ghost" :disabled="loading" @click="loadData">刷新列表</UiButton>
    </template>
  </AppPageHeader>

  <AppAlert v-if="feedback" variant="success" :title="feedback" />
  <AppAlert v-if="errorMessage" variant="error" :title="errorMessage" />

  <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
    <div
      v-for="item in summaryCards"
      :key="item.label"
      class="app-surface p-4"
    >
      <p class="text-sm text-slate-500">{{ item.label }}</p>
      <p class="mt-3 text-2xl font-semibold text-slate-900">{{ item.value }}</p>
      <p class="mt-2 text-xs leading-6 text-slate-500">{{ item.hint }}</p>
    </div>
  </div>

  <AppLoading v-if="loading" />

  <div v-else class="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
    <AppCard title="邀请码列表" description="邀请码默认单次使用，消耗后会自动标记为已使用。">
      <AppEmpty
        v-if="!inviteCodes.length"
        title="还没有邀请码"
        description="先生成一批邀请码，前台注册页就能用邀请码完成注册。"
      />
      <UiTable v-else>
        <thead>
          <tr>
            <th>邀请码</th>
            <th>状态</th>
            <th>备注</th>
            <th>创建时间</th>
            <th>到期时间</th>
            <th>使用情况</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in inviteCodes" :key="item.id">
            <td>
              <div class="space-y-1">
                <code class="font-semibold text-slate-900">{{ item.code }}</code>
                <p class="text-xs text-slate-500">创建人：{{ item.createdByName }}</p>
              </div>
            </td>
            <td>
              <span :class="['inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold', statusClasses(item.status)]">
                {{ statusLabel(item.status) }}
              </span>
            </td>
            <td class="text-sm text-slate-600">{{ item.note || '无备注' }}</td>
            <td class="whitespace-nowrap text-sm text-slate-500">{{ formatDateTime(item.createdAt) }}</td>
            <td class="whitespace-nowrap text-sm text-slate-500">{{ formatOptionalDateTime(item.expiresAt) }}</td>
            <td>
              <div class="space-y-1 text-sm text-slate-500">
                <p>{{ item.usedByName || '未使用' }}</p>
                <p v-if="item.usedAt">{{ formatDateTime(item.usedAt) }}</p>
              </div>
            </td>
            <td>
              <div class="flex flex-wrap gap-2">
                <UiButton size="sm" variant="ghost" @click="copyCode(item.code)">
                  {{ copiedCode === item.code ? '已复制' : '复制' }}
                </UiButton>
                <UiButton
                  v-if="item.canRevoke"
                  size="sm"
                  variant="danger"
                  @click="handleRevoke(item)"
                >
                  停用
                </UiButton>
              </div>
            </td>
          </tr>
        </tbody>
      </UiTable>
    </AppCard>

    <div class="space-y-6">
      <AppCard
        title="生成邀请码"
        description="建议平时按需生成，备注里写清来源或用途，后续排查会更轻松。"
      >
        <div class="space-y-4">
          <div>
            <label class="app-field-label">生成数量</label>
            <UiSelect
              v-model="form.count"
              :options="[
                { label: '1 个', value: '1' },
                { label: '3 个', value: '3' },
                { label: '5 个', value: '5' },
                { label: '10 个', value: '10' },
              ]"
            />
          </div>

          <div>
            <label class="app-field-label">备注</label>
            <UiInput v-model="form.note" placeholder="例如：四月新成员 / 上传组备用" />
          </div>

          <div>
            <label class="app-field-label">过期时间</label>
            <UiInput v-model="form.expiresAt" type="datetime-local" />
            <p class="mt-2 text-xs leading-6 text-slate-500">留空表示不过期，适合长期保留的内部邀请入口。</p>
          </div>
        </div>

        <template #footer>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <UiButton variant="ghost" :disabled="creating" @click="resetForm">重置表单</UiButton>
            <UiButton variant="primary" :disabled="creating" @click="handleCreate">
              {{ creating ? '生成中...' : '生成邀请码' }}
            </UiButton>
          </div>
        </template>
      </AppCard>

      <AppCard
        v-if="latestCreatedCodes.length"
        title="本次生成"
        description="邀请码只在这里完整展示一次，复制后发给成员即可。"
      >
        <div class="space-y-3">
          <div
            v-for="item in latestCreatedCodes"
            :key="item.id"
            class="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <div class="min-w-0">
              <code class="block truncate text-base font-semibold text-slate-900">{{ item.code }}</code>
              <p class="mt-1 text-xs text-slate-500">{{ item.note || '未填写备注' }}</p>
            </div>
            <UiButton size="sm" variant="secondary" @click="copyCode(item.code)">复制</UiButton>
          </div>
        </div>
      </AppCard>
    </div>
  </div>
</template>
