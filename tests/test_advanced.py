import tempfile, unittest
from pathlib import Path
from infinity_os.tool_registry import ToolRegistry
from infinity_os.contracts import ToolResult
from infinity_os.workflows import WorkflowEngine
from infinity_os.router2 import Router2
from infinity_os.core import InfinityCore

class DummySecurity:
    def decision(self,p):return 'allow'

class AdvancedTests(unittest.TestCase):
    def test_workflow_dependencies(self):
        tools=ToolRegistry();order=[]
        tools.register('one','one','',lambda: (order.append('one') or ToolResult(True,'one')))
        tools.register('two','two','',lambda: (order.append('two') or ToolResult(True,'two')))
        w=WorkflowEngine(tools,DummySecurity());item=w.create('test',[{'tool':'one','args':{}},{'tool':'two','args':{}}],0,True);res=w.run(item['id']);self.assertTrue(res['ok']);self.assertEqual(order,['one','two']);w.delete(item['id'])
    def test_router_feedback(self):
        c=InfinityCore()
        try:
            name=c.router.providers()[0]['name'];before=c.router._stat(name).get('arena_votes',0);c.router.record_arena_feedback(name,1);self.assertEqual(c.router._stat(name)['arena_votes'],before+1)
        finally:c.shutdown()
    def test_tools_have_schemas(self):
        c=InfinityCore()
        try:
            specs={x['name']:x for x in c.tools.specs()};self.assertIn('windows.open_app',specs);self.assertTrue(any(a['name']=='name' for a in specs['windows.open_app']['args']))
        finally:c.shutdown()

if __name__=='__main__':unittest.main()
