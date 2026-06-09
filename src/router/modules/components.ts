import { $t } from "@/plugins/i18n";
import { components } from "@/router/enums";

export default {
  path: "/components",
  redirect: "/components/dialog",
  meta: {
    icon: "ep/menu",
    title: $t("menus.pureComponents"),
    rank: components
  },
  children: [
    // 可在此基础上，添加路由，补充预设的各种模块页面 -- 见pure_admin 源项目
  ]
} satisfies RouteConfigsTable;

