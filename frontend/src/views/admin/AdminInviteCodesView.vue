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

type ExportSource = 'latest' | 'available' | 'all';

const inviteCodes = ref<InviteCode[]>([]);
const loading = ref(true);
const creating = ref(false);
const feedback = ref('');
const errorMessage = ref('');
const copiedCode = ref('');
const copiedLink = ref('');
const latestCreatedCodes = ref<InviteCode[]>([]);
const exportBaseUrl = ref(typeof window === 'undefined' ? '' : window.location.origin);
const includeRegisterLink = ref(true);
const exportSource = ref<ExportSource>('available');

const form = reactive({
  count: '1',
  note: '',
  expiresAt: '',
});

const availableInviteCodes = computed(() => inviteCodes.value.filter((item) => item.status === 'available'));

const summaryCards = computed(() => [
  {
    label: '全部邀请码',
    value: inviteCodes.value.length,
    hint: '包含可用、已使用、已过期和已停用的邀请码。',
  },
  {
    label: '当前可用',
    value: availableInviteCodes.value.length,
    hint: '还能继续发给成员注册的单次邀请码。',
  },
  {
    label: '已完成注册',
    value: inviteCodes.value.filter((item) => item.status === 'used').length,
    hint: '已经被成员消耗并成功完成注册的邀请码。',
  },
  {
    label: '已失效',
    value: inviteCodes.value.filter((item) => item.status === 'expired' || item.status === 'revoked').length,
    hint: '已过期或被管理员手动停用的邀请码。',
  },
]);

const exportOptions = computed(() => [
  {
    label: `本次新生成${latestCreatedCodes.value.length ? `（${latestCreatedCodes.value.length}）` : ''}`,
    value: 'latest',
  },
  {
    label: `当前可用（${availableInviteCodes.value.length}）`,
    value: 'available',
  },
  {
    label: `全部邀请码（${inviteCodes.value.length}）`,
    value: 'all',
  },
]);

const exportCandidates = computed(() => {
  if (exportSource.value === 'latest') {
    return latestCreatedCodes.value;
  }
  if (exportSource.value === 'all') {
    return inviteCodes.value;
  }
  return availableInviteCodes.value;
});

const exportLabel = computed(() => (includeRegisterLink.value ? '注册链接' : '邀请码'));

const exportHint = computed(() => {
  if (!exportCandidates.value.length) {
    if (exportSource.value === 'latest') {
      return '本次还没有新生成的邀请码，先生成一批后再导出。';
    }
    if (exportSource.value === 'all') {
      return '当前还没有邀请码数据可供导出。';
    }
    return '当前没有可用的邀请码。';
  }

  return `即将导出 ${exportCandidates.value.length} 条${exportLabel.value}。`;
});

const exportPreview = computed(() => {
  if (!exportCandidates.value.length) {
    return '';
  }

  return buildExportContent(exportCandidates.value)
    .split('\n')
    .slice(0, 3)
    .join('\n');
});

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

function normalizeRegisterBaseUrl(value: string) {
  const fallback = typeof window === 'undefined' ? '' : window.location.origin;
  const raw = value.trim() || fallback;

  if (!raw) {
    return '';
  }

  return raw.replace(/\/+$/u, '').replace(/\/register$/iu, '');
}

function buildInviteLink(code: string) {
  const baseUrl = normalizeRegisterBaseUrl(exportBaseUrl.value);
  const path = `/register?code=${encodeURIComponent(code)}`;
  return baseUrl ? `${baseUrl}${path}` : path;
}

function buildExportContent(items: InviteCode[]) {
  return items
    .map((item) => (includeRegisterLink.value ? buildInviteLink(item.code) : item.code))
    .join('\n');
}

function downloadTextFile(fileName: string, content: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const objectUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');

  anchor.href = objectUrl;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(objectUrl);
}

async function copyText(content: string, successMessage: string) {
  if (typeof navigator === 'undefined' || !navigator.clipboard) {
    throw new Error('clipboard-unavailable');
  }

  await navigator.clipboard.writeText(content);
  feedback.value = successMessage;
  errorMessage.value = '';
}

async function copyCode(code: string) {
  try {
    await copyText(code, `邀请码 ${code} 已复制。`);
    copiedCode.value = code;
    copiedLink.value = '';
  } catch {
    errorMessage.value = '复制失败，请手动复制邀请码。';
  }
}

async function copyLink(code: string) {
  try {
    await copyText(buildInviteLink(code), `邀请码 ${code} 的注册链接已复制。`);
    copiedLink.value = code;
    copiedCode.value = '';
  } catch {
    errorMessage.value = '复制注册链接失败，请稍后再试。';
  }
}

async function copyBatch() {
  if (!exportCandidates.value.length) {
    errorMessage.value = '当前没有可复制的内容。';
    feedback.value = '';
    return;
  }

  try {
    await copyText(
      buildExportContent(exportCandidates.value),
      `已批量复制 ${exportCandidates.value.length} 条${exportLabel.value}。`,
    );
    copiedCode.value = '';
    copiedLink.value = '';
  } catch {
    errorMessage.value = '批量复制失败，请手动导出文本文件。';
  }
}

function exportBatch() {
  if (!exportCandidates.value.length) {
    errorMessage.value = '当前没有可导出的内容。';
    feedback.value = '';
    return;
  }

  const content = buildExportContent(exportCandidates.value);
  const datePart = new Date().toISOString().slice(0, 10);
  const fileName = `invite-${exportSource.value}-${includeRegisterLink.value ? 'links' : 'codes'}-${datePart}.txt`;

  downloadTextFile(fileName, content);
  feedback.value = `已导出 ${exportCandidates.value.length} 条${exportLabel.value}。`;
  errorMessage.value = '';
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
    exportSource.value = 'latest';
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
    latestCreatedCodes.value = latestCreatedCodes.value.map((code) =>
      code.id === item.id
        ? {
            ...code,
            status: 'revoked',
            isActive: false,
            canRevoke: false,
          }
        : code,
    );
    feedback.value = `邀请码 ${item.code} 已停用。`;
    await loadData();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '停用邀请码失败。';
  }
}

onMounted(loadData);
</script>

<template>
  <AppPageHeader
    title="邀请码管理"
    description="关闭公开注册后，站点会自动切换为邀请码注册。这里可以批量生成、复制、导出和停用邀请码。"
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
        description="先生成一批邀请码，前台注册页就能使用邀请码完成注册。"
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
                  {{ copiedCode === item.code ? '已复制代码' : '复制代码' }}
                </UiButton>
                <UiButton size="sm" variant="secondary" @click="copyLink(item.code)">
                  {{ copiedLink === item.code ? '已复制链接' : '复制链接' }}
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
        description="建议按需生成，并在备注里写清来源或用途，后续排查会更轻松。"
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
        title="批量复制与导出"
        description="可以直接导出邀请码，也可以带上注册链接，发出去后成员点开就会自动带上邀请码。"
      >
        <div class="space-y-4">
          <div>
            <label class="app-field-label">导出范围</label>
            <UiSelect v-model="exportSource" :options="exportOptions" />
          </div>

          <div>
            <label class="app-field-label">注册链接前缀</label>
            <UiInput
              v-model="exportBaseUrl"
              placeholder="例如：https://ptsite.291277.xyz"
            />
            <p class="mt-2 text-xs leading-6 text-slate-500">
              支持直接填写站点域名，也支持填写到 <code>/register</code>；导出时会自动整理成注册链接。
            </p>
          </div>

          <label class="invite-export-toggle">
            <input v-model="includeRegisterLink" type="checkbox" class="invite-export-toggle__input" />
            <span>
              <span class="invite-export-toggle__title">导出时附带注册链接</span>
              <span class="invite-export-toggle__hint">
                开启后会导出形如 {{ buildInviteLink('XXXXXXX') }} 的内容。
              </span>
            </span>
          </label>

          <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p class="text-sm font-medium text-slate-900">{{ exportHint }}</p>
            <pre v-if="exportPreview" class="invite-export-preview">{{ exportPreview }}</pre>
          </div>
        </div>

        <template #footer>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <UiButton variant="secondary" :disabled="!exportCandidates.length" @click="copyBatch">
              批量复制{{ exportLabel }}
            </UiButton>
            <UiButton variant="primary" :disabled="!exportCandidates.length" @click="exportBatch">
              导出 {{ exportLabel }}.txt
            </UiButton>
          </div>
        </template>
      </AppCard>

      <AppCard
        v-if="latestCreatedCodes.length"
        title="本次生成"
        description="邀请码会在这里完整展示一轮，适合立即复制或直接导出注册链接。"
      >
        <div class="space-y-3">
          <div
            v-for="item in latestCreatedCodes"
            :key="item.id"
            class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div class="min-w-0">
                <code class="block truncate text-base font-semibold text-slate-900">{{ item.code }}</code>
                <p class="mt-1 text-xs text-slate-500">{{ item.note || '未填写备注' }}</p>
                <a
                  :href="buildInviteLink(item.code)"
                  target="_blank"
                  rel="noreferrer"
                  class="mt-2 block break-all text-xs text-blue-600 hover:text-blue-700"
                >
                  {{ buildInviteLink(item.code) }}
                </a>
              </div>
              <div class="flex flex-wrap gap-2">
                <UiButton size="sm" variant="ghost" @click="copyCode(item.code)">复制代码</UiButton>
                <UiButton size="sm" variant="secondary" @click="copyLink(item.code)">复制链接</UiButton>
              </div>
            </div>
          </div>
        </div>
      </AppCard>
    </div>
  </div>
</template>

<style scoped>
.invite-export-toggle {
  display: flex;
  gap: 0.85rem;
  border: 1px solid rgb(var(--border));
  border-radius: 1rem;
  background: rgb(var(--surface-muted));
  padding: 0.9rem 1rem;
}

.invite-export-toggle__input {
  margin-top: 0.2rem;
  height: 1rem;
  width: 1rem;
  accent-color: rgb(var(--primary));
}

.invite-export-toggle__title {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--text-primary));
}

.invite-export-toggle__hint {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  line-height: 1.6;
  color: rgb(var(--text-secondary));
}

.invite-export-preview {
  margin-top: 0.75rem;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 0.8rem;
  line-height: 1.7;
  color: rgb(var(--text-tertiary));
}
</style>
