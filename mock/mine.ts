import { defineFakeRoute } from "vite-plugin-fake-server/client";
import { faker } from "@faker-js/faker/locale/zh_CN";

export default defineFakeRoute([
  // 账户设置-个人信息
  {
    url: "/mine",
    method: "get",
    response: () => {
      return {
        success: true,
        data: {
          avatar:
            "https://ts1.tc.mm.bing.net/th/id/R-C.6752d8261b772d2ae652cddf6f0c1033?rik=BD0F%2be6e3IVD1w&riu=http%3a%2f%2fvorcdn.xiaodutv.com%2f1bcc05e7fcf5669800611ae52611e306&ehk=cWrp9DD6vLS4SvHJwK2FS6p0hrxTwr8n1y6vJ7p9u3w%3d&risl=&pid=ImgRaw&r=0",
          username: "admin",
          nickname: "admin",
          email: "XXX",
          phone: "XXX",
          description: "   "
        }
      };
    }
  },
  // 账户设置-个人安全日志
  {
    url: "/mine-logs",
    method: "get",
    response: () => {
      const list = [
        {
          id: 1,
          ip: faker.internet.ipv4(),
          address: "中国河南省信阳市",
          system: "macOS",
          browser: "Chrome",
          summary: "账户登录", // 详情
          operatingTime: new Date() // 时间
        },
        {
          id: 2,
          ip: faker.internet.ipv4(),
          address: "中国广东省深圳市",
          system: "Windows",
          browser: "Firefox",
          summary: "绑定了手机号码",
          operatingTime: new Date().setDate(new Date().getDate() - 1)
        }
      ];
      return {
        success: true,
        data: {
          list,
          total: list.length, // 总条目数
          pageSize: 10, // 每页显示条目个数
          currentPage: 1 // 当前页数
        }
      };
    }
  }
]);
