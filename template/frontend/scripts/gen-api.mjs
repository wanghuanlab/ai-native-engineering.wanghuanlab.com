// 由 contracts/openapi/<模块>.yaml 生成前端接口客户端，输出到 packages/api-client/src/generated/<模块>.ts
// 生成结果不入库、不手改；契约变更后重新执行 pnpm gen:api
import { existsSync, readdirSync, readFileSync, rmSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { generate } from 'orval'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const contractsDir = resolve(root, '../contracts/openapi')
const outDir = resolve(root, 'packages/api-client/src/generated')
const mutator = resolve(root, 'packages/api-client/src/http.ts')

// 新模块的契约骨架为 paths: {}，没有接口时跳过
const modules = readdirSync(contractsDir)
  .filter((f) => f.endsWith('.yaml') && f !== 'common.yaml')
  .filter((f) => !/^paths:\s*\{\s*\}\s*$/m.test(readFileSync(resolve(contractsDir, f), 'utf8')))
  .map((f) => f.replace(/\.yaml$/, ''))

rmSync(outDir, { recursive: true, force: true })

for (const name of modules) {
  const target = resolve(outDir, `${name}.ts`)
  await generate({
    input: {
      target: resolve(contractsDir, `${name}.yaml`),
      parserOptions: { externalRefs: { allow: ['./common.yaml'] } },
    },
    output: {
      target,
      client: 'axios-functions',
      prettier: true,
      override: { mutator: { path: mutator, name: 'request' } },
    },
  })
  if (!existsSync(target)) {
    console.error(`生成失败：${name}.yaml，请查看上方 orval 输出`)
    process.exit(1)
  }
}

console.warn(`已生成 ${modules.length} 个模块的接口客户端：${modules.join(', ') || '（无）'}`)
