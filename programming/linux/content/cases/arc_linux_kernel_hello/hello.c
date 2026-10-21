#include <linux/init.h>
#include <linux/module.h>

//#include <config/modversions.h>

#include <linux/kernel.h>


//static int __init hello_init(void) {
//	printk(KERN_DEBUG "Hello World, Kernel 郭雅 !!!\n");
//	return 0;
//}
//
//static void cleanup_module(void) {
//	printk(KERN_DEBUG "GoodBye, curel Kernel !!!\n");
////	return 0;
//}


static int __init hello_init() {
	printk(KERN_EMERG, "Hello world kernel 郭雅\n");
	return 0;
}

static void __exit hello_exit() {
	printk(KERN_EMERG "GoodBye, cruel world \n");
}

module_init(hello_init);
module_exit(hello_exit);
