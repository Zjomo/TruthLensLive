<script setup lang="ts">
import { useI18n } from "vue-i18n";
import Motion from "./utils/motion";
import { useRouter } from "vue-router";
import { message } from "@/utils/message";
import { loginRules } from "./utils/rule";
import TypeIt from "@/components/ReTypeit";
import { debounce } from "@pureadmin/utils";
import { useNav } from "@/layout/hooks/useNav";
import { useEventListener } from "@vueuse/core";
import type { FormInstance } from "element-plus";
import { $t, transformI18n } from "@/plugins/i18n";
import { operates, thirdParty } from "./utils/enums";
import { useLayout } from "@/layout/hooks/useLayout";
import LoginPhone from "./components/LoginPhone.vue";
import LoginRegist from "./components/LoginRegist.vue";
import LoginUpdate from "./components/LoginUpdate.vue";
import LoginQrCode from "./components/LoginQrCode.vue";
import { useUserStoreHook } from "@/store/modules/user";
import { initRouter, getTopMenu } from "@/router/utils";
import { bg, avatar, illustration } from "./utils/static";
import { ReImageVerify } from "@/components/ReImageVerify";
import { ref, toRaw, reactive, watch, computed, onMounted } from "vue";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { useTranslationLang } from "@/layout/hooks/useTranslationLang";
import { useDataThemeChange } from "@/layout/hooks/useDataThemeChange";

import dayIcon from "@/assets/svg/day.svg?component";
import darkIcon from "@/assets/svg/dark.svg?component";
import globalization from "@/assets/svg/globalization.svg?component";
import Lock from "~icons/ri/lock-fill";
import Check from "~icons/ep/check";
import User from "~icons/ri/user-3-fill";
import Info from "~icons/ri/information-line";
import Keyhole from "~icons/ri/shield-keyhole-line";
import { getConfig } from "@/config";

defineOptions({
  name: "Login"
});


const MottoText = getConfig("MottoText");
const MottoSubtext = getConfig("MottoSubtext");
const WelcomeText = getConfig("WelcomeText");
const imgCode = ref("");
const loginDay = ref(7);
const router = useRouter();
const loading = ref(false);
const checked = ref(false);
const disabled = ref(false);
const ruleFormRef = ref<FormInstance>();
const currentPage = computed(() => {
  return useUserStoreHook().currentPage;
});

const { t } = useI18n();
const { initStorage } = useLayout();
initStorage();
const { dataTheme, overallStyle, dataThemeChange } = useDataThemeChange();
dataThemeChange(overallStyle.value);
const { title, getDropdownItemStyle, getDropdownItemClass } = useNav();
const { locale, translationCh, translationEn } = useTranslationLang();

const ruleForm = reactive({
  username: "admin",
  password: "admin123",
  verifyCode: ""
});

const onLogin = async (formEl: FormInstance | undefined) => {
  if (!formEl) return;
  await formEl.validate(valid => {
    if (valid) {
      loading.value = true;
      useUserStoreHook()
        .loginByUsername({
          username: ruleForm.username,
          password: ruleForm.password
        })
        .then(res => {
          if (res.success) {
            // 获取后端路由
            return initRouter().then(() => {
              disabled.value = true;
              router
                .push(getTopMenu(true).path)
                .then(() => {
                  message(t("login.pureLoginSuccess"), { type: "success" });
                })
                .finally(() => (disabled.value = false));
            });
          } else {
            message(t("login.pureLoginFail"), { type: "error" });
          }
        })
        .finally(() => (loading.value = false));
    }
  });
};

const immediateDebounce: any = debounce(
  formRef => onLogin(formRef),
  1000,
  true
);

useEventListener(document, "keydown", ({ code }) => {
  if (
    ["Enter", "NumpadEnter"].includes(code) &&
    !disabled.value &&
    !loading.value
  )
    immediateDebounce(ruleFormRef.value);
});

watch(imgCode, value => {
  useUserStoreHook().SET_VERIFYCODE(value);
});
watch(checked, bool => {
  useUserStoreHook().SET_ISREMEMBERED(bool);
});
watch(loginDay, value => {
  useUserStoreHook().SET_LOGINDAY(value);
});

// 粒子背景初始化
onMounted(() => {
  if (typeof window !== 'undefined') {
    const canvas = document.getElementById('particle-canvas') as HTMLCanvasElement;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      if (ctx) {
        // 粒子数组
        const particles: any[] = [];
        const particleCount = 80;

        for (let i = 0; i < particleCount; i++) {
          particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 2 + 1,
            speedX: (Math.random() - 0.5) * 0.5,
            speedY: (Math.random() - 0.5) * 0.5,
            color: `rgba(255, 255, 255, ${Math.random() * 0.5 + 0.1})`
          });
        }

        function animate() {
          if (!ctx) return;

          ctx.clearRect(0, 0, canvas.width, canvas.height);

          // 绘制渐变背景
          const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
          gradient.addColorStop(0, '#0061ff');
          gradient.addColorStop(1, '#60efff');
          ctx.fillStyle = gradient;
          ctx.fillRect(0, 0, canvas.width, canvas.height);

          // 更新并绘制粒子
          particles.forEach(p => {
            p.x += p.speedX;
            p.y += p.speedY;

            // 边界检查
            if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
            if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
          });

          requestAnimationFrame(animate);
        }

        animate();
      }
    }
  }
});
</script>

<template>
  <div class="select-none login-container">
    <!-- 粒子背景画布 -->
    <canvas id="particle-canvas" class="fixed top-0 left-0 w-full h-full z-0"></canvas>

    <div class="absolute top-5 right-5 z-10">
      <!-- 主题切换 -->
      <el-tooltip effect="dark" :content="dataTheme ? '深色模式' : '浅色模式'" placement="bottom">
        <el-switch
          v-model="dataTheme"
          inline-prompt
          :active-icon="dayIcon"
          :inactive-icon="darkIcon"
          @change="dataThemeChange"
          class="theme-switch"
        />
      </el-tooltip>

      <!-- 国际化 -->
      <el-dropdown trigger="click" class="ml-3">
        <globalization
          class="global-icon hover:text-primary w-[24px] h-[24px] cursor-pointer"
        />
        <template #dropdown>
          <el-dropdown-menu class="translation">
            <el-dropdown-item
              :style="getDropdownItemStyle(locale, 'zh')"
              :class="['dark:text-white!', getDropdownItemClass(locale, 'zh')]"
              @click="translationCh"
            >
              <IconifyIconOffline
                v-show="locale === 'zh'"
                class="check-zh"
                :icon="Check"
              />
              简体中文
            </el-dropdown-item>
            <el-dropdown-item
              :style="getDropdownItemStyle(locale, 'en')"
              :class="['dark:text-white!', getDropdownItemClass(locale, 'en')]"
              @click="translationEn"
            >
              <span v-show="locale === 'en'" class="check-en">
                <IconifyIconOffline :icon="Check" />
              </span>
              English
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="login-content z-10">
      <!-- 文化馆信息面板 -->
      <div class="history-panel">
        <div class="university-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 100 100" class="logo-svg">
              <circle cx="50" cy="50" r="45" fill="#0066FF" opacity="0.2" />
              <path d="M30,30 L70,30 L70,70 L30,70 Z" fill="none" stroke="#FFF" stroke-width="3" />
              <path d="M40,40 L60,40 L60,60 L40,60 Z" fill="none" stroke="#FFF" stroke-width="2" />
              <circle cx="50" cy="50" r="15" fill="none" stroke="#FFF" stroke-width="2" />
            </svg>
          </div>
        </div>
        <div class="motto">
          <p class="motto-text">{{MottoText}}</p>
          <p class="motto-subtext">{{MottoSubtext}}</p>
          <br><br><br><br><br><br><br><br><br><br>
          <p class="motto-text"></p>
        </div>
        <!--
        <div class="timeline">
          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <span>1925</span>
              <p>学校创立</p>
            </div>
          </div>
          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <span>1952</span>
              <p>院系调整</p>
            </div>
          </div>
          <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <span>2000</span>
              <p>新校区建成</p>
            </div>
          </div>
        </div>

      -->
      <!-- 登录卡片 -->
      </div>
      <div class="login-card">
        <div class="card-header">
          <avatar class="avatar" />
          <Motion>
            <h2 class="university-title">
              <TypeIt
                :options="{ strings: [title], cursor: false, speed: 100 }"
              />
            </h2>
          </Motion>
          <p class="welcome-text">{{WelcomeText}}</p>
        </div>

        <el-form
          v-if="currentPage === 0"
          ref="ruleFormRef"
          :model="ruleForm"
          :rules="loginRules"
          size="large"
          class="login-form"
        >
          <Motion :delay="100">
            <el-form-item
              :rules="[
                {
                  required: true,
                  message: transformI18n($t('login.pureUsernameReg')),
                  trigger: 'blur'
                }
              ]"
              prop="username"
            >
              <el-input
                v-model="ruleForm.username"
                clearable
                :placeholder="t('login.pureUsername')"
                :prefix-icon="useRenderIcon(User)"
                class="custom-input"
              />
            </el-form-item>
          </Motion>

          <Motion :delay="150">
            <el-form-item prop="password">
              <el-input
                v-model="ruleForm.password"
                clearable
                show-password
                :placeholder="t('login.purePassword')"
                :prefix-icon="useRenderIcon(Lock)"
                class="custom-input"
              />
            </el-form-item>
          </Motion>

          <Motion :delay="200">
            <el-form-item prop="verifyCode">
              <el-input
                v-model="ruleForm.verifyCode"
                clearable
                :placeholder="t('login.pureVerifyCode')"
                :prefix-icon="useRenderIcon(Keyhole)"
                class="custom-input"
              >
                <template v-slot:append>
                  <ReImageVerify v-model:code="imgCode" />
                </template>
              </el-input>
            </el-form-item>
          </Motion>

          <Motion :delay="250">
            <el-form-item>
              <div class="w-full h-[20px] flex justify-between items-center remember-section">
                <!--
                <el-checkbox v-model="checked" class="remember-checkbox">
                  <span class="remember-text">
                    <select
                      v-model="loginDay"
                      class="remember-select"
                    >
                      <option value="1">1</option>
                      <option value="7">7</option>
                      <option value="30">30</option>
                    </select>
                    {{ t("login.pureRemember") }}
                    <IconifyIconOffline
                      v-tippy="{
                        content: t('login.pureRememberInfo'),
                        placement: 'top'
                      }"
                      :icon="Info"
                      class="ml-1 info-icon"
                    />
                  </span>
                </el-checkbox>
                -->
                <el-button
                  link
                  type="primary"
                  class="forgot-password"
                  @click="useUserStoreHook().SET_CURRENTPAGE(4)"
                >
                  {{ t("login.pureForget") }}
                </el-button>
              </div>
              <el-button
                class="w-full mt-6 login-button"
                size="default"
                type="primary"
                :loading="loading"
                :disabled="disabled"
                @click="onLogin(ruleFormRef)"
              >
                {{ t("login.pureLogin") }}
              </el-button>
            </el-form-item>
          </Motion>


          <Motion :delay="300">
            <el-form-item>
              <div class="w-full flex justify-between items-center mt-4">
                <el-button
                  v-for="(item, index) in operates"
                  :key="index"
                  class="flex-1 mx-1 operation-button"
                  size="default"
                  @click="useUserStoreHook().SET_CURRENTPAGE(index + 1)"
                >
                  {{ t(item.title) }}
                </el-button>
              </div>
            </el-form-item>
          </Motion>
        </el-form>

        <!-- 手机号登录 -->
        <LoginPhone v-if="currentPage === 1" />
        <!-- 二维码登录 -->
        <LoginQrCode v-if="currentPage === 2" />
        <!-- 注册 -->
        <LoginRegist v-if="currentPage === 3" />
        <!-- 忘记密码 -->
        <LoginUpdate v-if="currentPage === 4" />
      </div>
    </div>

    <!-- 底部版权信息 -->
    <div class="copyright">
      Copyright © 2025 -present
      <a
        class="hover:text-primary"
        target="_blank"
      >
        &nbsp;{{ title }}
      </a>
    </div>

    <!-- 装饰元素 -->
    <div class="decor decor-1"></div>
    <div class="decor decor-2"></div>
    <div class="decor decor-3"></div>
  </div>
</template>

<style scoped>
.login-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0061ff 0%, #60efff 100%);
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.login-content {
  display: flex;
  width: 90%;
  max-width: 1200px;
  height: 80vh;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.history-panel {
  width: 40%;
  padding: 40px;
  background: rgba(0, 33, 87, 0.7);
  color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.history-panel::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0 L100 100 M100 0 L0 100' stroke='rgba(255,255,255,0.05)' stroke-width='1'/%3E%3C/svg%3E");
  opacity: 0.3;
}

.university-logo {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.logo-svg {
  width: 80px;
  height: 80px;
}

.university-name {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 1px;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.motto {
  text-align: center;
  margin-bottom: 50px;
}

.motto-text {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 10px;
  letter-spacing: 2px;
}

.motto-subtext {
  font-size: 16px;
  opacity: 0.9;
}

.timeline {
  position: relative;
  padding-left: 30px;
}

.timeline::before {
  content: "";
  position: absolute;
  left: 7px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(255, 255, 255, 0.3);
}

.timeline-item {
  position: relative;
  margin-bottom: 30px;
}

.timeline-dot {
  position: absolute;
  left: 0;
  top: 5px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  transform: translateX(-50%);
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.3);
}

.timeline-content {
  margin-left: 30px;
}

.timeline-content span {
  font-size: 20px;
  font-weight: 700;
  display: block;
  margin-bottom: 5px;
}

.timeline-content p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.login-card {
  width: 60%;
  padding: 50px;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-header {
  text-align: center;
  margin-bottom: 40px;
}

.avatar {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  border-radius: 50%;
  border: 3px solid #0061ff;
  box-shadow: 0 5px 15px rgba(0, 97, 255, 0.3);
}

.university-title {
  font-size: 28px;
  font-weight: 700;
  color: #0061ff;
  margin: 0 0 10px;
}

.welcome-text {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.login-form {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.custom-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 0 15px;
  box-shadow: 0 2px 8px rgba(0, 97, 255, 0.1);
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
}

.custom-input :deep(.el-input__wrapper:hover),
.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: #0061ff;
  box-shadow: 0 2px 12px rgba(0, 97, 255, 0.2);
}

.remember-section {
  margin-bottom: 5px;
}

.remember-checkbox :deep(.el-checkbox__label) {
  color: #555;
  font-size: 14px;
}

.remember-select {
  width: 40px;
  outline: none;
  background: none;
  appearance: none;
  border: none;
  color: #0061ff;
  font-weight: 600;
  border-bottom: 1px dashed #0061ff;
  padding: 2px 0;
  margin-right: 3px;
  text-align: center;
  cursor: pointer;
}

.info-icon {
  color: #0061ff;
  vertical-align: middle;
}

.forgot-password {
  font-size: 14px;
  color: #0061ff;
}

.login-button {
  height: 48px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(90deg, #0061ff 0%, #60efff 100%);
  border: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 97, 255, 0.3);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 97, 255, 0.4);
}

.operation-button {
  height: 42px;
  border-radius: 8px;
  background: rgba(0, 97, 255, 0.1);
  color: #0061ff;
  border: 1px solid rgba(0, 97, 255, 0.2);
  transition: all 0.3s ease;
}

.operation-button:hover {
  background: rgba(0, 97, 255, 0.2);
  transform: translateY(-2px);
}

.copyright {
  position: absolute;
  bottom: 20px;
  width: 100%;
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  z-index: 10;
}

.copyright a {
  color: white;
  text-decoration: none;
  font-weight: 600;
}

.theme-switch {
  --el-switch-on-color: #0061ff;
  --el-switch-off-color: #aaa;
}

.global-icon {
  color: white;
  transition: all 0.3s ease;
}

.global-icon:hover {
  color: #60efff;
  transform: scale(1.1);
}

.decor {
  position: absolute;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  z-index: 1;
}

.decor-1 {
  width: 300px;
  height: 300px;
  top: -150px;
  right: -150px;
}

.decor-2 {
  width: 200px;
  height: 200px;
  bottom: 50px;
  left: -100px;
}

.decor-3 {
  width: 150px;
  height: 150px;
  bottom: -75px;
  right: 20%;
}

.translation {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
}

.translation ::v-deep(.el-dropdown-menu__item) {
  padding: 10px 20px;
  font-size: 14px;
  transition: all 0.3s;
}

.translation ::v-deep(.el-dropdown-menu__item:hover) {
  background: rgba(0, 97, 255, 0.1);
  color: #0061ff;
}

.check-zh, .check-en {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #0061ff;
}

/* 响应式调整 */
@media (max-width: 992px) {
  .history-panel {
    display: none;
  }

  .login-card {
    width: 100%;
    padding: 30px;
  }
}

@media (max-width: 576px) {
  .login-content {
    height: auto;
    margin: 20px;
  }

  .login-card {
    padding: 20px;
  }
}
</style>

<style lang="scss" scoped>
:deep(.el-input-group__append, .el-input-group__prepend) {
  padding: 0;
  background: #f5f7fa;
  border-left: none;
}

:deep(.el-image-verify) {
  height: 40px;
  border-radius: 0 10px 10px 0;
  overflow: hidden;
  cursor: pointer;
}
</style>
