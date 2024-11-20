## SSE

Similar to [OpenAI](https://platform.openai.com/docs/api-reference/streaming) the `/threads/{thread_id}/messages` endpoint only supports Server-Sent Events (SSE).

An SSE stream is simply a stream of message chunks with an `event` and `data` field.

For example:

```
event: delta
data: {"content": "Hello, world!"}

event: delta
data: {"content": "Hello, world! How are you?"}
```

See [MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#examples) for examples.