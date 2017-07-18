from aiosparql.syntax import Node, RDFTerm

from tests.integration.helpers import IntegrationTestCase, unittest_run_loop


class DeltaTestCase(IntegrationTestCase):
    @unittest_run_loop
    async def test_push_notification(self):
        ws = await self.client.ws_connect('/')
        test_id = self.uuid4()
        test_iri = self.resource("resource1", test_id)
        await self.insert_node(Node(test_iri, {
            "rdf:type": RDFTerm("push:Resource1"),
            "mu:uuid": test_id,
            "dct:title": "test",
            "push:number": 1,
        }))
        data = await ws.receive_json()
        self.assertIn('push', data)
        self.assertEqual(data['push']['data']['id'], test_id)

    @unittest_run_loop
    async def test_push_many_notifications(self):
        ws = await self.client.ws_connect('/')
        test1_id = self.uuid4()
        test1_iri = self.resource("resource1", test1_id)
        test2_id = self.uuid4()
        test2_iri = self.resource("resource1", test2_id)
        await self.insert_triples([
            Node(test1_iri, {
                "rdf:type": RDFTerm("push:Resource1"),
                "mu:uuid": test1_id,
                "dct:title": "test",
                "push:number": 1,
            }),
            Node(test2_iri, {
                "rdf:type": RDFTerm("push:Resource1"),
                "mu:uuid": test2_id,
                "dct:title": "test",
                "push:number": 2,
            }),
        ])
        data1 = await ws.receive_json()
        self.assertIn('push', data1)
        self.assertIn(data1['push']['data']['id'], (test1_id, test2_id))
        data2 = await ws.receive_json()
        self.assertIn('push', data2)
        self.assertIn(data2['push']['data']['id'], (test1_id, test2_id))

    @unittest_run_loop
    async def test_push_push_and_delete_notifications(self):
        ws = await self.client.ws_connect('/')
        test_id = self.uuid4()
        test_iri = self.resource("resource1", test_id)
        await self.insert_node(Node(test_iri, {
            "rdf:type": RDFTerm("push:Resource1"),
            "mu:uuid": test_id,
            "dct:title": "test",
            "push:number": 1,
        }))
        data1 = await ws.receive_json()
        self.assertIn('push', data1)
        self.assertEqual(data1['push']['data']['id'], test_id)
        await self.delete_node(test_iri)
        data2 = await ws.receive_json()
        self.assertIn('delete', data2)
        self.assertEqual(data2['delete']['data']['id'], test_id)
