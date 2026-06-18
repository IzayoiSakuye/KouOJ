
<script setup lang="ts">
  import { onMounted } from 'vue';
  import { RouterLink, RouterView, useRouter } from 'vue-router';
  import { useAuthStore } from './stores/auth';
  
  // 获取pinia的登陆状态仓库
  const authStore = useAuthStore() 
  // 拿到路由控制器，用于后面主动跳转页面
  const router = useRouter()

  // 控制登出
  function handleLogout()
  {
    authStore.logout()
    router.push('/login')
  }

  /**
   * 页面刷新后恢复用户信息
   * 刷新以后pinia中的user会丢掉，所以要从localStorage中拿取token
   * 当App启动时，如果发现有token，就请求GET api/auth/me
   */
  onMounted(()=>
  {
    if (authStore.isLoggedIn && !authStore.user)
    {
      authStore.loadMe().catch(()=>{authStore.logout()})
    }
  })

</script>

<!-- 导航栏 -->
<template>
  <header class="app-header">
    <nav class="app-nav">
      <RouterLink class="brand" to="/">KouOJ</RouterLink>

      <div class="nav-links">
        <RouterLink to="/problems">题目</RouterLink>
        <RouterLink to="/submissions">提交记录</RouterLink>
        <RouterLink v-if="authStore.user?.is_admin" to="/admin">管理</RouterLink>
      </div>

      <div class="nav-user">
        <template v-if="authStore.user">
          <RouterLink to="/profile">
            {{ authStore.user.nickname || authStore.user.username }}
          </RouterLink>
          <button type="button" @click="handleLogout">退出</button>
        </template>

        <template v-else>
          <RouterLink to="/login">登录</RouterLink>
          <RouterLink to="/register">注册</RouterLink>
        </template>
      </div>
    </nav>
  </header>

  <RouterView />
</template>

<!-- 导航栏样式 -->
<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

.app-nav {
  width: min(1120px, calc(100% - 32px));
  height: 56px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 24px;
}

.brand {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary);
}

.nav-links,
.nav-user {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-links {
  flex: 1;
}

a.router-link-active {
  color: var(--primary);
  font-weight: 600;
}

</style>
