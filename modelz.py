from gpt4all import GPT4All
model = GPT4All("orca-mini-3b.ggmlv3.q4_0.bin")
# https://huggingface.co/TheBloke/orca_mini_3B-GGML

def orca_mini_3b(prompt, max_tokens, temp, top_k, top_p, repeat_penalty, repeat_last_n, n_batch, n_predict, streaming):
    """
Args:
    prompt: The prompt for the model to complete.
    max_tokens: The maximum number of tokens to generate.
    temp: The model temperature. Larger values increase creativity but decrease factuality.
    top_k: Randomly sample from the top_k most likely tokens at each generation step. Set this to 1 for greedy decoding.
    top_p: Randomly sample at each generation step from the top most likely tokens whose probabilities add up to top_p.
    repeat_penalty: Penalize the model for repetition. Higher values result in less repetition.
    repeat_last_n: How far in the models generation history to apply the repeat penalty.
    n_batch: Number of prompt tokens processed in parallel. Larger values decrease latency but increase resource requirements.
    n_predict: Equivalent to max_tokens, exists for backwards compatibility.
    streaming: If True, this method will instead return a generator that yields tokens as the model generates them.

Returns:
    Either the entire completion or a generator that yields the completion token by token.
    """

    output = model.generate(prompt, max_tokens, temp, top_k, top_p, repeat_penalty, repeat_last_n, n_batch, n_predict, streaming)
    return output

if __name__ == "__main__":
    print(orca_mini_3b("Bayleef is a", 64, .7, 40, .2, 1.8, 128, 8, None, False ))
    print(orca_mini_3b("Bay leaf is a", 64, .7, 40, .2, 1.8, 128, 8, None, False ))