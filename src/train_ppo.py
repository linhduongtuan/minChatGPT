import click
import torch
from trainers import PPOTrainer
from configs import get_configs
from gpt import GPTActor, GPTRewardModel, GPTCritic
from dataset import DahoasSFTStaticPromptsDataset


def train(batch_size, exp_name):
    cfg = get_configs("gpt2-medium")
    cfg.actor_weights = "./runs/sft_gpt2medium-batch8-full_202303140623/sft_gpt2medium-batch8-full_202303140623_final.pt"
    # 67% gpt2-medium sft lora
    cfg.critic_weights = "./runs/rm-gpt2medium-lora-sft/rm-gpt2medium-lora-sft.pt"
    # 68% gpt2-xl
    # cfg.critic_weights = "./runs/rm_1678230899/rm_1678230899_final.pt"
    # 63%
    # cfg.critic_weights = "./runs/rm_gpt2medium-batch8-full-sft_202303141545/rm_gpt2medium-batch8-full-sft_202303141545_final.pt"
    cfg.reward_model_weights = cfg.critic_weights
    cfg.sft_model_weights = cfg.actor_weights
    cfg.batch_size = batch_size
    cfg.total_epochs = 2
    cfg.exp_name = exp_name

    actor = GPTActor.from_checkpoint(cfg, cfg.actor_weights).cuda()
    sft_model = GPTActor.from_checkpoint(cfg, cfg.sft_model_weights).cuda()

    cfg2 = get_configs("gpt2-medium/lora")
    critic = GPTCritic.from_checkpoint(cfg2, cfg.critic_weights).cuda()
    reward_model = GPTRewardModel.from_checkpoint(
        cfg2, cfg.reward_model_weights).cuda()

    reward_model.freeze_weights("lora")
    critic.freeze_weights("lora")

    dataset = DahoasSFTStaticPromptsDataset(block_size=1024,
                                            max_examples=None,
                                            tokenizer_name="tiktoken/gpt2")
    trainer = PPOTrainer(cfg, actor, critic, reward_model, sft_model, dataset)
    trainer.fit()


@click.command()
@click.option('--strategy', '-s')
@click.option('--batch-size', '-b', default=1)
@click.option('--exp-name', '-n', default="default")
def main(strategy, batch_size, exp_name):
    torch.manual_seed(1234)

    train(batch_size, exp_name)


if __name__ == "__main__":
    main()
