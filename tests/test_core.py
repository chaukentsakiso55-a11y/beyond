import json, tempfile, shutil, unittest
from pathlib import Path
from infinity_os.contracts import ToolResult
from infinity_os.tool_registry import ToolRegistry
from infinity_os.security import SecurityEngine
from infinity_os.workflows import WorkflowEngine
from infinity_os.memory2 import MemoryEngine2
from infinity_os.core import InfinityCore

class CoreTests(unittest.TestCase):
    def test_offline_agent_parser(self):
        c=InfinityCore()
        try:
            p=c.agent.plan('open Chrome then search for Qt docs then open VS Code')
            self.assertEqual([s.tool for s in p.steps],['windows.open_app','browser.search','windows.open_app'])
            p=c.agent.plan('open whatsapp and send a message to Alex saying hello')
            self.assertEqual(p.steps[0].tool,'messages.whatsapp')
            self.assertEqual(p.steps[0].permission,'messages.send')
        finally:c.shutdown()
    def test_memory_round_trip(self):
        c=InfinityCore()
        try:
            mid=c.memory.add('Infinity OS','Unit Test Memory','router memory workflow capability',['test'])
            rows=c.memory.search('workflow capability','Infinity OS',10)
            self.assertTrue(any(r['id']==mid for r in rows))
        finally:c.shutdown()
    def test_status(self):
        c=InfinityCore()
        try:
            s=c.status();self.assertEqual(s['version'],'7.9.0-ultimate');self.assertIn('cpu',s);self.assertIn('native',s)
        finally:c.shutdown()

if __name__=='__main__':unittest.main()
