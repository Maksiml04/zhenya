export default {
  async fetch() {
    return new Response('Gone', { status: 410 });
  },
};
