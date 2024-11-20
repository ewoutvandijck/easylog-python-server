# Installation

If you're running on MacOS, you can install the dependencies and virtual environment by running the following command:

```sh
$ ./install.sh
```

# How This API Works

This API allows users to initiate and manage chat sessions by creating a new thread through the `/threads` endpoint. A thread serves as a container for the chat history. You can associate a thread with your own identifier by providing an `external_id`, which can be used for future interactions with that thread.

Each thread includes a `messages` property, which is a list of messages. Every message has a `role` property (`user` or `assistant`) and a `content` property, which contains the message data. Assistant messages can include multiple content types, such as `text` and `image`.

For example, a thread with a user message and an assistant message might look like this:

```json
{
  "id": "cm3oo3qjn0000hhxabjc25i6i",
  "external_id": "example-external-id",
  "created_at": "2024-11-19T16:27:10.499000Z",
  "updated_at": "2024-11-19T16:27:10.499000Z",
  "messages": [
    {
      "id": "cm3pmxjf20000sic5g3o87zvd",
      "thread_id": "cm3oo3qjn0000hhxabjc25i6i",
      "role": "user",
      "contents": [
        {
          "id": "cm3pmxjf20001sic5oa0ihzc1",
          "message_id": "cm3pmxjf20000sic5g3o87zvd",
          "content_type": "text",
          "content": "Hello, how are you?",
          "created_at": "2024-11-20T08:42:07.886000Z",
          "updated_at": "2024-11-20T08:42:07.886000Z"
        }
      ],
      "agent_class": "OpenAIAssistant",
      "created_at": "2024-11-20T08:42:07.886000Z",
      "updated_at": "2024-11-20T08:42:07.886000Z"
    },
    {
      "id": "cm3pmxjf50002sic56pdp359d",
      "thread_id": "cm3oo3qjn0000hhxabjc25i6i",
      "role": "assistant",
      "contents": [
        {
          "id": "cm3pmxjf50003sic5eo5b8m0d",
          "message_id": "cm3pmxjf50002sic56pdp359d",
          "content_type": "text",
          "content": "Hello! I'm doing well, thank you. How can I assist you today?",
          "created_at": "2024-11-20T08:42:07.890000Z",
          "updated_at": "2024-11-20T08:42:07.890000Z"
        }
      ],
      "agent_class": "OpenAIAssistant",
      "created_at": "2024-11-20T08:42:07.890000Z",
      "updated_at": "2024-11-20T08:42:07.890000Z"
    }
  ]
}
```

You can find the full API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## Message Routing and Agent Configuration

When creating a message, you can specify an `agent_config` property that determines which agent will handle the response generation. The message will be automatically routed to the appropriate agent based on this configuration. The agent then processes the message and generates a response according to its capabilities and settings.

Example message with agent configuration:

```json
{
  "agent_config": {
    "agent_class": "OpenAIAssistant",
    "assistant_id": "asst_5vWL7aefIopE4aU5DcFRmpA5"
  },
  "content": [
    {
      "content": "Hello, how are you?",
      "type": "text"
    }
  ]
}
```

## Understanding Message Streams


The `/threads/{thread_id}/messages` endpoint supports **Server-Sent Events (SSE)**, similar to [OpenAI's streaming API](https://platform.openai.com/docs/api-reference/streaming).

An SSE stream sends a sequence of message chunks, each containing an `event` and `data` field. Here's an example of SSE output:

```
event: delta
data: {"content": "Hello, world!"}

event: delta
data: {"content": "Hello, world! How are you?"}
```

> For more information on Server-Sent Events and implementation examples, visit [MDN's SSE documentation](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#examples).


The streaming process does not immediately provide the full message content. Instead, it sends a series of events, each representing a small piece (chunk) of the assistant's response. These chunks are aggregated and stored in the `content` property once the stream finishes.

For example, if the assistant responds with "Hello, world!", the stream might emit three events like this:

```
event: delta
data: {"type": "text", "text": "Hello", "chunk_index": 0}

event: delta
data: {"type": "text", "text": "world", "chunk_index": 0}

event: delta
data: {"type": "text", "text": "!", "chunk_index": 0}
```

These chunks are grouped by `chunk_index` and consolidated into the final message content:

```json
{
    "type": "text",
    "content": "Hello, world!"
}
```

> Currently, we only support text deltas, but this might change in the future. For example, we might support image deltas.

When an error occurs, the stream will emit an `error` event with the error message.

For example:

```
event: error
data: {"details": "The agent failed to generate a response"}
```

Once the stream is complete, the message is added to the thread's `messages` list. You can retrieve the full message content by calling the `/threads/{thread_id}/messages` endpoint.
