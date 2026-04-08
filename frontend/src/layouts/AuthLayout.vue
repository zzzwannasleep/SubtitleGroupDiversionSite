<template>
  <div class="min-h-screen bg-slate-100">
    <div class="mx-auto flex min-h-screen max-w-5xl items-center justify-center px-4 py-12">
      <div class="grid w-full gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <div class="hidden rounded-3xl bg-slate-900 p-10 text-white shadow-2xl lg:block">
          <p class="text-sm uppercase tracking-[0.24em] text-slate-400">Subtitle Group Diversion</p>
          <h1 class="mt-6 text-4xl font-semibold leading-tight">内部资源浏览、RSS 订阅与权限管理统一入口</h1>
          <p class="mt-6 max-w-md text-sm leading-7 text-slate-300">
            前端按游客层、登录用户层、上传者层和管理层拆分，使用三套布局与统一状态组件。
          </p>
        </div>
        <div class="flex items-center">
          <div class="w-full">
            <RouterView />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

