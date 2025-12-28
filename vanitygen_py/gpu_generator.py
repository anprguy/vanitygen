import threading
import time
import queue
# Handle both module and direct execution
try:
    from .bitcoin_keys import BitcoinKey
except ImportError:
    from bitcoin_keys import BitcoinKey

try:
    import pyopencl as cl
except ImportError:
    cl = None

class GPUGenerator:
    def __init__(self, prefix, addr_type='p2pkh'):
        self.prefix = prefix
        self.addr_type = addr_type
        self.result_queue = queue.Queue()
        self.running = False
        self.search_thread = None
        self.stats_counter = 0
        self.stats_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.gpu_available = False

    def init_cl(self):
        try:
            platforms = cl.get_platforms()
            if not platforms:
                return False
            self.device = platforms[0].get_devices()[0]
            self.ctx = cl.Context([self.device])
            self.queue = cl.CommandQueue(self.ctx)
            return True
        except Exception as e:
            print(f"OpenCL initialization failed: {e}")
            return False

    def is_available(self):
        return self.gpu_available

    def _search_loop(self):
        while not self.stop_event.is_set():
            key = BitcoinKey()
            if self.addr_type == 'p2pkh':
                address = key.get_p2pkh_address()
            elif self.addr_type == 'p2wpkh':
                address = key.get_p2wpkh_address()
            elif self.addr_type == 'p2sh-p2wpkh':
                address = key.get_p2sh_p2wpkh_address()
            else:
                address = key.get_p2pkh_address()

            if address.startswith(self.prefix):
                self.result_queue.put((address, key.get_wif(), key.get_public_key().hex()))

            with self.stats_lock:
                self.stats_counter += 1

    def start(self):
        if self.running:
            return

        self.stop_event.clear()
        self.stats_counter = 0

        # Try to initialize OpenCL, but run CPU fallback even if unavailable
        self.gpu_available = self.init_cl()

        if self.gpu_available:
            print("GPU acceleration available, using CPU fallback for now")
        else:
            print("GPU acceleration not available, using CPU fallback")

        self.running = True
        self.search_thread = threading.Thread(target=self._search_loop, daemon=True)
        self.search_thread.start()

    def stop(self):
        if not self.running:
            return

        self.stop_event.set()
        self.running = False

        if self.search_thread and self.search_thread.is_alive():
            self.search_thread.join(timeout=1.0)

    def get_stats(self):
        with self.stats_lock:
            count = self.stats_counter
            self.stats_counter = 0
            return count
