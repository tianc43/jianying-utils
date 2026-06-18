import { useEffect } from "react";
import { useAtom, useAtomValue, useSetAtom } from "jotai";
import { open } from "@tauri-apps/plugin-dialog";
import {
  Alert,
  Badge,
  Box,
  Button,
  Checkbox,
  Code,
  Container,
  Divider,
  Group,
  Paper,
  Stack,
  Text,
  TextInput,
  Title,
  Tooltip,
} from "@mantine/core";
import { CheckCircle2, Download, FolderOpen, Info, LoaderCircle, RotateCcw, TriangleAlert } from "lucide-react";
import {
  appendLogAtom,
  canInstallAtom,
  clearRunStateAtom,
  draftNameAtom,
  draftsDirAtom,
  installingAtom,
  logsAtom,
  overwriteAtom,
  placeholderIdAtom,
  resultAtom,
  sourceAtom,
} from "./state";
import { getEnvironmentInfo, installDraft } from "./tauri";

export default function App() {
  const [source, setSource] = useAtom(sourceAtom);
  const [draftsDir, setDraftsDir] = useAtom(draftsDirAtom);
  const [draftName, setDraftName] = useAtom(draftNameAtom);
  const [placeholderId, setPlaceholderId] = useAtom(placeholderIdAtom);
  const [overwrite, setOverwrite] = useAtom(overwriteAtom);
  const [installing, setInstalling] = useAtom(installingAtom);
  const result = useAtomValue(resultAtom);
  const logs = useAtomValue(logsAtom);
  const canInstall = useAtomValue(canInstallAtom);
  const appendLog = useSetAtom(appendLogAtom);
  const clearRunState = useSetAtom(clearRunStateAtom);
  const setResult = useSetAtom(resultAtom);

  useEffect(() => {
    getEnvironmentInfo()
      .then((info) => {
        if (info.defaultDraftsDir) {
          setDraftsDir(info.defaultDraftsDir);
          appendLog({ level: "info", message: `已识别剪映草稿目录：${info.defaultDraftsDir}` });
        }
        if (info.detectedPlaceholderId) {
          appendLog({ level: "success", message: `已识别本机占位符：${info.detectedPlaceholderId}` });
        }
      })
      .catch((error) => {
        appendLog({ level: "error", message: `环境检测失败：${String(error)}` });
      });
  }, [appendLog, setDraftsDir]);

  async function chooseDraftsDir() {
    const selected = await open({ directory: true, multiple: false, title: "选择剪映草稿目录" });
    if (typeof selected === "string") {
      setDraftsDir(selected);
    }
  }

  async function onInstall() {
    clearRunState();
    setInstalling(true);
    appendLog({ level: "info", message: "开始下载并导入草稿。" });
    try {
      const installResult = await installDraft({
        source: source.trim(),
        draftsDir: draftsDir.trim(),
        draftName: draftName.trim() || undefined,
        placeholderId: placeholderId.trim() || undefined,
        overwrite,
      });
      setResult(installResult);
      appendLog({ level: "success", message: `导入完成：${installResult.targetDir}` });
    } catch (error) {
      appendLog({ level: "error", message: String(error) });
    } finally {
      setInstalling(false);
    }
  }

  return (
    <Box className="app-shell">
      <Container size="lg" py="xl">
        <Group justify="space-between" align="flex-end" mb="lg">
          <div>
            <Group gap="sm" mb={6}>
              <Title order={1}>jy-downloader</Title>
              <Badge variant="filled" color="teal">Preview</Badge>
            </Group>
            <Text c="dimmed" size="sm">下载服务端便携草稿包，并在本机转换成剪映可识别的草稿。</Text>
          </div>
          <Tooltip label="重置本次导入日志和结果">
            <Button variant="subtle" leftSection={<RotateCcw size={16} />} onClick={clearRunState}>
              清空
            </Button>
          </Tooltip>
        </Group>

        <div className="workspace">
          <Paper withBorder radius="sm" p="lg" className="panel">
            <Stack gap="md">
              <Title order={2}>导入参数</Title>
              <TextInput
                label="草稿下载 URL 或本地 ZIP"
                placeholder="http://server/drafts/<draft_id>/download"
                value={source}
                onChange={(event) => setSource(event.currentTarget.value)}
                leftSection={<Download size={16} />}
              />
              <TextInput
                label="剪映草稿目录"
                placeholder="D:\\jianying\\JianyingPro Drafts"
                value={draftsDir}
                onChange={(event) => setDraftsDir(event.currentTarget.value)}
                rightSection={
                  <Tooltip label="选择目录">
                    <button className="icon-button" onClick={chooseDraftsDir} type="button">
                      <FolderOpen size={16} />
                    </button>
                  </Tooltip>
                }
              />
              <TextInput
                label="导入后的草稿名"
                placeholder="留空则使用草稿包内名称"
                value={draftName}
                onChange={(event) => setDraftName(event.currentTarget.value)}
              />
              <TextInput
                label="占位符 ID"
                placeholder="留空则自动扫描本机剪映草稿"
                value={placeholderId}
                onChange={(event) => setPlaceholderId(event.currentTarget.value)}
              />
              <Checkbox
                label="覆盖同名草稿目录"
                checked={overwrite}
                onChange={(event) => setOverwrite(event.currentTarget.checked)}
              />
              <Button
                leftSection={installing ? <LoaderCircle className="spin" size={16} /> : <Download size={16} />}
                disabled={!canInstall}
                onClick={onInstall}
                fullWidth
              >
                {installing ? "正在导入" : "下载并导入"}
              </Button>
            </Stack>
          </Paper>

          <Stack gap="md">
            <Paper withBorder radius="sm" p="lg" className="panel">
              <Group gap="sm" mb="sm">
                <Info size={18} />
                <Title order={2}>状态</Title>
              </Group>
              {result ? (
                <Alert color="teal" icon={<CheckCircle2 size={18} />} title="草稿已准备好">
                  <Stack gap={6}>
                    <Text size="sm">草稿：<Code>{result.draftName}</Code></Text>
                    <Text size="sm">路径：<Code>{result.targetDir}</Code></Text>
                    <Text size="sm">占位符：<Code>{result.placeholderId}</Code></Text>
                  </Stack>
                </Alert>
              ) : (
                <Alert color="gray" icon={<TriangleAlert size={18} />} title="等待导入">
                  <Text size="sm">填写 URL 和草稿目录后开始导入。首次使用前，请确保剪映里至少存在一个本机草稿。</Text>
                </Alert>
              )}
            </Paper>

            <Paper withBorder radius="sm" p="lg" className="panel log-panel">
              <Group justify="space-between" mb="sm">
                <Title order={2}>运行日志</Title>
                <Badge variant="light">{logs.length}</Badge>
              </Group>
              <Divider mb="sm" />
              <Stack gap={8}>
                {logs.length === 0 ? (
                  <Text c="dimmed" size="sm">暂无日志。</Text>
                ) : (
                  logs.map((log) => (
                    <Text key={log.id} size="sm" className={`log-line log-${log.level}`}>
                      {log.message}
                    </Text>
                  ))
                )}
              </Stack>
            </Paper>
          </Stack>
        </div>
      </Container>
    </Box>
  );
}
