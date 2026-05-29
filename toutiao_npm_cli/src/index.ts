#!/usr/bin/env node
import { Command } from 'commander';
import { loginCommand } from './commands/login';
import { postCommand } from './commands/post';
import { crawlCommand } from './commands/crawl';

const program = new Command();

program
  .name('toutiao')
  .description('今日头条 CLI 工具 - 发布微头条和文章')
  .version('1.0.0');

program.addCommand(loginCommand);
program.addCommand(postCommand);
program.addCommand(crawlCommand);

program.parse(process.argv);
